"""
TorqCare Backend - Main FastAPI Application
Multi-Agent Orchestrator for Autonomous Vehicle Care
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import asyncio
import json
import random

from agents.orchestrator import AgentOrchestrator
from agents.data_analysis_agent import DataAnalysisAgent
from agents.diagnosis_agent import DiagnosisAgent
from agents.customer_engagement_agent import CustomerEngagementAgent
from agents.scheduling_agent import SchedulingAgent
from agents.quality_insights_agent import QualityInsightsAgent
from agents.feedback_agent import FeedbackAgent
from database.connection import get_db_session
from database.models import SensorData, MaintenanceHistory, Appointment, Feedback
from ml_models.prediction_model import VehicleFailurePredictionModel

app = FastAPI(title="TorqCare API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents and orchestrator
orchestrator = AgentOrchestrator()
data_agent = DataAnalysisAgent()
diagnosis_agent = DiagnosisAgent()
engagement_agent = CustomerEngagementAgent()
scheduling_agent = SchedulingAgent()
quality_agent = QualityInsightsAgent()
feedback_agent = FeedbackAgent()

# Register agents with orchestrator
orchestrator.register_agent("data_analysis", data_agent)
orchestrator.register_agent("diagnosis", diagnosis_agent)
orchestrator.register_agent("customer_engagement", engagement_agent)
orchestrator.register_agent("scheduling", scheduling_agent)
orchestrator.register_agent("quality_insights", quality_agent)
orchestrator.register_agent("feedback", feedback_agent)

# Initialize ML model
ml_model = VehicleFailurePredictionModel()

# Pydantic Models
class SensorDataInput(BaseModel):
    vehicle_id: str
    engine_temp: float
    rpm: float
    fuel_level: float
    tire_pressure_fl: float
    tire_pressure_fr: float
    tire_pressure_rl: float
    tire_pressure_rr: float
    battery_voltage: float
    oil_pressure: float
    brake_fluid_level: float
    speed: float

class ChatMessage(BaseModel):
    vehicle_id: str
    message: str
    context: Optional[Dict] = None

class AppointmentRequest(BaseModel):
    vehicle_id: str
    issue_type: str
    urgency: str
    preferred_date: Optional[str] = None

class FeedbackSubmission(BaseModel):
    vehicle_id: str
    appointment_id: int
    feedback_type: str
    rating: int
    comment: str

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# API Endpoints

@app.get("/")
async def root():
    return {
        "service": "TorqCare API",
        "version": "1.0.0",
        "status": "operational",
        "agents": orchestrator.get_agent_status()
    }

@app.post("/api/sensor-data")
async def receive_sensor_data(data: SensorDataInput):
    """
    Receive real-time sensor data from vehicle
    Triggers data analysis and anomaly detection
    """
    try:
        # Store in database
        db = next(get_db_session())
        sensor_record = SensorData(
            vehicle_id=data.vehicle_id,
            timestamp=datetime.now(),
            engine_temp=data.engine_temp,
            rpm=data.rpm,
            fuel_level=data.fuel_level,
            tire_pressure_fl=data.tire_pressure_fl,
            tire_pressure_fr=data.tire_pressure_fr,
            tire_pressure_rl=data.tire_pressure_rl,
            tire_pressure_rr=data.tire_pressure_rr,
            battery_voltage=data.battery_voltage,
            oil_pressure=data.oil_pressure,
            brake_fluid_level=data.brake_fluid_level,
            speed=data.speed
        )
        db.add(sensor_record)
        db.commit()
        
        # Trigger agent analysis
        analysis_result = await orchestrator.process_sensor_data(data.dict())
        
        # Check for anomalies and predictions
        if analysis_result.get("anomalies"):
            # Trigger diagnosis agent
            diagnosis = await orchestrator.diagnose_issue(data.dict(), analysis_result)
            
            # If critical, trigger scheduling agent
            if diagnosis.get("severity") == "critical":
                appointment = await orchestrator.schedule_appointment(
                    vehicle_id=data.vehicle_id,
                    issue=diagnosis,
                    urgency="critical"
                )
                
                # Broadcast to connected clients
                await manager.broadcast({
                    "type": "critical_alert",
                    "data": {
                        "vehicle_id": data.vehicle_id,
                        "diagnosis": diagnosis,
                        "appointment": appointment
                    }
                })
        
        return {
            "status": "success",
            "analysis": analysis_result,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vehicle/{vehicle_id}/telemetry")
async def get_vehicle_telemetry(vehicle_id: str, limit: int = 100):
    """Get recent telemetry data for a vehicle"""
    db = next(get_db_session())
    records = db.query(SensorData).filter(
        SensorData.vehicle_id == vehicle_id
    ).order_by(SensorData.timestamp.desc()).limit(limit).all()
    
    return {"vehicle_id": vehicle_id, "data": records}

@app.post("/api/predict-failures")
async def predict_failures(data: SensorDataInput):
    """
    Use ML model to predict potential mechanical failures
    """
    try:
        # Prepare data for ML model
        features = ml_model.prepare_features(data.dict())
        
        # Get predictions
        predictions = ml_model.predict(features)
        
        # If high-risk predictions, notify quality insights agent
        if any(pred["probability"] > 0.7 for pred in predictions):
            await quality_agent.report_potential_failure(
                vehicle_id=data.vehicle_id,
                predictions=predictions
            )
        
        return {
            "vehicle_id": data.vehicle_id,
            "predictions": predictions,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_with_assistant(message: ChatMessage):
    """
    Customer engagement chatbot endpoint
    Handles queries about telemetry, maintenance, and vehicle info
    """
    try:
        # Get current vehicle data
        db = next(get_db_session())
        latest_sensor = db.query(SensorData).filter(
            SensorData.vehicle_id == message.vehicle_id
        ).order_by(SensorData.timestamp.desc()).first()
        
        # Process through engagement agent
        response = await engagement_agent.process_query(
            message=message.message,
            vehicle_id=message.vehicle_id,
            sensor_data=latest_sensor.__dict__ if latest_sensor else None,
            context=message.context
        )
        
        return {
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/appointments")
async def create_appointment(request: AppointmentRequest):
    """
    Schedule appointment with automatic slot suggestion
    """
    try:
        # Get available slots from scheduling agent
        available_slots = await scheduling_agent.get_available_slots(
            urgency=request.urgency,
            issue_type=request.issue_type,
            preferred_date=request.preferred_date
        )
        
        # Create pending appointment
        db = next(get_db_session())
        appointment = Appointment(
            vehicle_id=request.vehicle_id,
            issue_type=request.issue_type,
            urgency=request.urgency,
            status="pending",
            suggested_slots=json.dumps(available_slots),
            created_at=datetime.now()
        )
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        
        return {
            "appointment_id": appointment.id,
            "available_slots": available_slots,
            "status": "pending_confirmation"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/appointments/{appointment_id}/confirm")
async def confirm_appointment(appointment_id: int, selected_slot: Dict):
    """Confirm appointment with selected time slot"""
    try:
        db = next(get_db_session())
        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id
        ).first()
        
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        appointment.status = "confirmed"
        appointment.scheduled_time = datetime.fromisoformat(selected_slot["datetime"])
        appointment.workshop_id = selected_slot["workshop_id"]
        db.commit()
        
        # Notify workshop
        await scheduling_agent.notify_workshop(appointment_id, selected_slot)
        
        return {"status": "confirmed", "appointment": appointment}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/feedback")
async def submit_feedback(feedback: FeedbackSubmission):
    """
    Submit feedback on repair/vehicle performance
    Triggers feedback agent to share with manufacturer and workshop
    """
    try:
        db = next(get_db_session())
        
        # Store feedback
        feedback_record = Feedback(
            vehicle_id=feedback.vehicle_id,
            appointment_id=feedback.appointment_id,
            feedback_type=feedback.feedback_type,
            rating=feedback.rating,
            comment=feedback.comment,
            submitted_at=datetime.now()
        )
        db.add(feedback_record)
        db.commit()
        db.refresh(feedback_record)
        
        # Process through feedback agent
        await feedback_agent.process_feedback(feedback.dict())
        
        # Share with quality insights agent
        await quality_agent.ingest_feedback(feedback.dict())
        
        return {
            "status": "success",
            "feedback_id": feedback_record.id,
            "message": "Feedback shared with manufacturer and workshop"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/quality-insights")
async def get_quality_insights(vehicle_model: Optional[str] = None):
    """
    Get manufacturing quality insights
    Aggregated failure patterns and feedback analysis
    """
    try:
        insights = await quality_agent.generate_insights(vehicle_model)
        return insights
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/maintenance-history/{vehicle_id}")
async def get_maintenance_history(vehicle_id: str):
    """Get maintenance and repair history"""
    db = next(get_db_session())
    history = db.query(MaintenanceHistory).filter(
        MaintenanceHistory.vehicle_id == vehicle_id
    ).order_by(MaintenanceHistory.service_date.desc()).all()
    
    return {"vehicle_id": vehicle_id, "history": history}

@app.websocket("/ws/telemetry/{vehicle_id}")
async def websocket_telemetry(websocket: WebSocket, vehicle_id: str):
    """
    WebSocket endpoint for real-time telemetry streaming
    """
    await manager.connect(websocket)
    try:
        while True:
            # Simulate real-time data (replace with actual sensor stream)
            data = {
                "vehicle_id": vehicle_id,
                "timestamp": datetime.now().isoformat(),
                "engine_temp": 75 + random.uniform(-5, 25),
                "rpm": 800 + random.uniform(0, 3000),
                "battery_voltage": 12.5 + random.uniform(-1, 1.5),
                "speed": random.uniform(0, 120)
            }
            await websocket.send_json(data)
            await asyncio.sleep(3)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/agents/status")
async def get_agents_status():
    """Get status of all agents in the network"""
    return orchestrator.get_agent_status()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)