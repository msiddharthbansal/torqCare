"""
TorqCare FastAPI Backend Server
Multi-agent orchestration for vehicle care management
"""

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncio
import pandas as pd
import os

# Import agents
from agents.data_analysis_agent import DataAnalysisAgent
from agents.diagnosis_agent import DiagnosisAgent
from agents.chatbot_agent import ChatbotAgent
from agents.scheduling_agent import SchedulingAgent
from agents.quality_insights_agent import QualityInsightsAgent
from agents.feedback_agent import FeedbackAgent

# Import database
from database.database import get_db, init_db
from database.models import (
    Vehicle, SensorReading, MaintenanceRecord,
    Appointment, Workshop, Feedback, Alert
)

# Import ML models
from models.predictive_models import VehicleFailurePredictor

# Initialize FastAPI
app = FastAPI(
    title="TorqCare API",
    description="Autonomous multi-agent network for vehicle care",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
data_agent = DataAnalysisAgent()
diagnosis_agent = DiagnosisAgent()
chatbot_agent = ChatbotAgent()
scheduling_agent = SchedulingAgent()
quality_agent = QualityInsightsAgent()
feedback_agent = FeedbackAgent()

# ML predictor
ml_predictor = VehicleFailurePredictor()
try:
    ml_predictor.load_models()
except:
    print("⚠ ML models not found, will use fallback predictions")

# WebSocket connections
active_connections: Dict[str, WebSocket] = {}

# ==================== STARTUP ====================
@app.on_event("startup")
async def startup_event():
    """Initialize database and load data"""
    print("🚀 Starting TorqCare Server...")
    init_db()
    print("✓ Database initialized")

# ==================== VEHICLES ====================
@app.get("/api/vehicles")
async def get_vehicles(db: Session = Depends(get_db)):
    """Get all vehicles"""
    vehicles = db.query(Vehicle).all()
    return vehicles

@app.get("/api/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: str, db: Session = Depends(get_db)):
    """Get specific vehicle details"""
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@app.get("/api/vehicles/{vehicle_id}/health")
async def get_vehicle_health(vehicle_id: str, db: Session = Depends(get_db)):
    """Get vehicle health summary"""
    # Get recent sensor readings
    readings = db.query(SensorReading)\
        .filter(SensorReading.vehicle_id == vehicle_id)\
        .order_by(SensorReading.timestamp.desc())\
        .limit(100)\
        .all()
    
    if not readings:
        raise HTTPException(status_code=404, detail="No sensor data found")
    
    # Convert to dict list
    readings_dict = [r.__dict__ for r in readings]
    
    # Get health summary
    health = data_agent.get_vehicle_health_summary(readings_dict)
    
    return health

# ==================== SENSOR DATA ====================
@app.get("/api/sensor/{vehicle_id}/latest")
async def get_latest_sensor_data(vehicle_id: str, db: Session = Depends(get_db)):
    """Get latest sensor reading"""
    reading = db.query(SensorReading)\
        .filter(SensorReading.vehicle_id == vehicle_id)\
        .order_by(SensorReading.timestamp.desc())\
        .first()
    
    if not reading:
        raise HTTPException(status_code=404, detail="No sensor data found")
    
    return reading

@app.get("/api/sensor/{vehicle_id}/history")
async def get_sensor_history(
    vehicle_id: str,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get historical sensor data"""
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    readings = db.query(SensorReading)\
        .filter(
            SensorReading.vehicle_id == vehicle_id,
            SensorReading.timestamp >= cutoff_time
        )\
        .order_by(SensorReading.timestamp.desc())\
        .all()
    
    return readings

@app.get("/api/sensor/{vehicle_id}/analyze")
async def analyze_sensor_data(vehicle_id: str, db: Session = Depends(get_db)):
    """Analyze current sensor data for anomalies"""
    reading = db.query(SensorReading)\
        .filter(SensorReading.vehicle_id == vehicle_id)\
        .order_by(SensorReading.timestamp.desc())\
        .first()
    
    if not reading:
        raise HTTPException(status_code=404, detail="No sensor data found")
    
    # Analyze with data agent
    analysis = data_agent.analyze_sensor_reading(reading.__dict__)
    
    # Generate report
    report = await data_agent.generate_analysis_report(analysis)
    analysis['report'] = report
    
    return analysis

# ==================== DIAGNOSIS ====================
@app.post("/api/diagnosis/{vehicle_id}")
async def diagnose_vehicle(vehicle_id: str, db: Session = Depends(get_db)):
    """Run comprehensive vehicle diagnosis"""
    # Get latest sensor reading
    reading = db.query(SensorReading)\
        .filter(SensorReading.vehicle_id == vehicle_id)\
        .order_by(SensorReading.timestamp.desc())\
        .first()
    
    if not reading:
        raise HTTPException(status_code=404, detail="No sensor data found")
    
    # Analyze for anomalies
    analysis = data_agent.analyze_sensor_reading(reading.__dict__)
    
    # Run diagnosis
    diagnosis = diagnosis_agent.diagnose_vehicle(reading.__dict__, analysis['anomalies'])
    
    # Generate diagnosis report
    report = await diagnosis_agent.generate_diagnosis_report(diagnosis)
    diagnosis['report'] = report
    
    # Get maintenance plan
    if diagnosis['issues']:
        plan = diagnosis_agent.generate_maintenance_plan(diagnosis)
        diagnosis['maintenance_plan'] = plan
    
    # Create alert if critical
    if any(i['severity'] == 'Critical' for i in diagnosis.get('issues', [])):
        alert = Alert(
            vehicle_id=vehicle_id,
            alert_type='Critical Issue',
            severity='Critical',
            component=diagnosis['issues'][0]['component'],
            message=f"Critical issue detected: {diagnosis['issues'][0]['component']}",
            recommendation=report
        )
        db.add(alert)
        db.commit()
    
    return diagnosis

# ==================== CHATBOT ====================
@app.post("/api/chat/{vehicle_id}")
async def chat_with_bot(
    vehicle_id: str,
    message: str,
    db: Session = Depends(get_db)
):
    """Chat with vehicle assistant"""
    # Get vehicle data
    reading = db.query(SensorReading)\
        .filter(SensorReading.vehicle_id == vehicle_id)\
        .order_by(SensorReading.timestamp.desc())\
        .first()
    
    # Get diagnosis
    diagnosis = None
    if reading:
        analysis = data_agent.analyze_sensor_reading(reading.__dict__)
        if analysis['status'] == 'Anomaly Detected':
            diagnosis = diagnosis_agent.diagnose_vehicle(reading.__dict__, analysis['anomalies'])
    
    # Chat
    response = await chatbot_agent.chat(
        vehicle_id,
        message,
        vehicle_data=reading.__dict__ if reading else None,
        diagnosis=diagnosis
    )
    
    return {"response": response}

# ==================== APPOINTMENTS ====================
@app.get("/api/workshops")
async def get_workshops(db: Session = Depends(get_db)):
    """Get all service workshops"""
    workshops = db.query(Workshop).all()
    return workshops

@app.post("/api/appointments/propose/{vehicle_id}")
async def propose_appointment(vehicle_id: str, db: Session = Depends(get_db)):
    """Propose appointment based on diagnosis"""
    # Run diagnosis
    reading = db.query(SensorReading)\
        .filter(SensorReading.vehicle_id == vehicle_id)\
        .order_by(SensorReading.timestamp.desc())\
        .first()
    
    if not reading:
        raise HTTPException(status_code=404, detail="No sensor data found")
    
    analysis = data_agent.analyze_sensor_reading(reading.__dict__)
    diagnosis = diagnosis_agent.diagnose_vehicle(reading.__dict__, analysis['anomalies'])
    
    # Get workshops
    workshops = db.query(Workshop).all()
    workshops_dict = [w.__dict__ for w in workshops]
    
    # Create proposal
    proposal = await scheduling_agent.create_appointment_proposal(
        vehicle_id,
        diagnosis,
        workshops_dict
    )
    
    return proposal

@app.post("/api/appointments/confirm")
async def confirm_appointment(
    vehicle_id: str,
    appointment_data: Dict,
    db: Session = Depends(get_db)
):
    """Confirm and book appointment"""
    # Create appointment
    appointment = scheduling_agent.confirm_appointment(
        vehicle_id,
        appointment_data,
        appointment_data.get('notes')
    )
    
    # Save to database
    db_appointment = Appointment(
        appointment_id=appointment['appointment_id'],
        vehicle_id=vehicle_id,
        workshop_id=appointment['workshop_id'],
        scheduled_date=datetime.fromisoformat(appointment['scheduled_datetime']),
        estimated_duration_hours=appointment['estimated_duration_hours'],
        service_type='Repair',
        status='Confirmed',
        estimated_cost=appointment['estimated_cost'][0]
    )
    db.add(db_appointment)
    db.commit()
    
    return appointment

@app.get("/api/appointments/{vehicle_id}")
async def get_appointments(vehicle_id: str, db: Session = Depends(get_db)):
    """Get vehicle appointments"""
    appointments = db.query(Appointment)\
        .filter(Appointment.vehicle_id == vehicle_id)\
        .order_by(Appointment.scheduled_date.desc())\
        .all()
    
    return appointments

# ==================== MAINTENANCE ====================
@app.get("/api/maintenance/{vehicle_id}")
async def get_maintenance_history(vehicle_id: str, db: Session = Depends(get_db)):
    """Get maintenance history"""
    records = db.query(MaintenanceRecord)\
        .filter(MaintenanceRecord.vehicle_id == vehicle_id)\
        .order_by(MaintenanceRecord.maintenance_date.desc())\
        .all()
    
    return records

# ==================== FEEDBACK ====================
@app.post("/api/feedback")
async def submit_feedback(feedback_data: Dict, db: Session = Depends(get_db)):
    """Submit feedback on repair"""
    # Process feedback
    processed = await feedback_agent.process_feedback(feedback_data)
    
    # Save to database
    db_feedback = Feedback(
        feedback_id=f"FBK-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        vehicle_id=feedback_data['vehicle_id'],
        maintenance_id=feedback_data.get('maintenance_id'),
        rating=feedback_data['rating'],
        sentiment=processed['sentiment'],
        comment=feedback_data['comment'],
        repair_effectiveness=feedback_data.get('repair_effectiveness', 3),
        service_quality=feedback_data.get('service_quality', 3),
        communication_rating=feedback_data.get('communication_rating', 3)
    )
    db.add(db_feedback)
    db.commit()
    
    # Share with manufacturer if needed
    if processed['share_with_manufacturer']:
        await quality_agent.process_feedback(feedback_data)
    
    return {"status": "success", "processed": processed}

# ==================== QUALITY INSIGHTS ====================
@app.get("/api/insights")
async def get_quality_insights(db: Session = Depends(get_db)):
    """Get quality insights for manufacturer"""
    # Get recent maintenance records
    records = db.query(MaintenanceRecord)\
        .order_by(MaintenanceRecord.maintenance_date.desc())\
        .limit(200)\
        .all()
    
    # Analyze patterns
    insights = await quality_agent.generate_insights([r.__dict__ for r in records])
    
    return insights

# ==================== WEBSOCKET ====================
@app.websocket("/ws/{vehicle_id}")
async def websocket_endpoint(websocket: WebSocket, vehicle_id: str):
    """Real-time sensor data streaming"""
    await websocket.accept()
    active_connections[vehicle_id] = websocket
    
    try:
        while True:
            # Simulate real-time data (in production, this would come from vehicle)
            await asyncio.sleep(10)
            
            # Get latest reading from DB
            # In production: stream actual telemetry
            data = {"vehicle_id": vehicle_id, "timestamp": datetime.now().isoformat()}
            
            await websocket.send_json(data)
    
    except WebSocketDisconnect:
        del active_connections[vehicle_id]

# ==================== HEALTH CHECK ====================
@app.get("/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "agents": {
            "data_analysis": "active",
            "diagnosis": "active",
            "chatbot": "active",
            "scheduling": "active",
            "quality_insights": "active",
            "feedback": "active"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
