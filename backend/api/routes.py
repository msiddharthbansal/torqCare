"""
Complete API Routes for TorqCare Backend
Handles all endpoints for frontend-backend communication
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import sys
sys.path.append('..')

from database.database import get_db
from database.models import (
    Vehicle, SensorReading, MaintenanceRecord,
    Appointment, Workshop, Feedback, Alert
)
from agents.data_analysis_agent import DataAnalysisAgent
from agents.diagnosis_agent import DiagnosisAgent
from agents.chatbot_agent import ChatbotAgent
from agents.scheduling_agent import SchedulingAgent
from agents.quality_insights_agent import QualityInsightsAgent
from agents.feedback_agent import FeedbackAgent

# Initialize router
router = APIRouter()

# Initialize agents (singleton pattern)
data_agent = DataAnalysisAgent()
diagnosis_agent = DiagnosisAgent()
chatbot_agent = ChatbotAgent()
scheduling_agent = SchedulingAgent()
quality_agent = QualityInsightsAgent()
feedback_agent = FeedbackAgent()

# ==================== PYDANTIC MODELS ====================

class VehicleResponse(BaseModel):
    vehicle_id: str
    model: str
    year: int
    owner_name: Optional[str]
    status: str
    total_distance_km: float
    
    class Config:
        from_attributes = True

class HealthResponse(BaseModel):
    vehicle_id: str
    overall_health: float
    component_health: dict
    last_updated: str
    distance_traveled: float
    status: str

class SensorResponse(BaseModel):
    vehicle_id: str
    timestamp: datetime
    soc: float
    soh: float
    battery_temp: float
    motor_temp: float
    motor_vibration: float
    brake_pad_wear: float
    
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    timestamp: str

class AppointmentConfirmRequest(BaseModel):
    workshop_id: str
    workshop_name: str
    date: str
    time: str
    estimated_duration: int
    estimated_cost_min: int
    estimated_cost_max: int
    notes: Optional[str] = None

class FeedbackRequest(BaseModel):
    vehicle_id: str
    maintenance_id: Optional[str]
    rating: int
    comment: str
    repair_effectiveness: int
    service_quality: int
    communication_rating: int

# ==================== VEHICLES ====================

@router.get("/vehicles", response_model=List[VehicleResponse])
async def get_vehicles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all vehicles with pagination"""
    try:
        vehicles = db.query(Vehicle).offset(skip).limit(limit).all()
        return vehicles
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(vehicle_id: str, db: Session = Depends(get_db)):
    """Get specific vehicle details"""
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@router.get("/vehicles/{vehicle_id}/health", response_model=HealthResponse)
async def get_vehicle_health(vehicle_id: str, db: Session = Depends(get_db)):
    """Get vehicle health summary"""
    # Verify vehicle exists
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Get recent sensor readings
    readings = db.query(SensorReading)\
        .filter(SensorReading.vehicle_id == vehicle_id)\
        .order_by(SensorReading.timestamp.desc())\
        .limit(100)\
        .all()
    
    if not readings:
        raise HTTPException(status_code=404, detail="No sensor data found")
    
    # Convert to dict list
    readings_dict = [{
        'vehicle_id': r.vehicle_id,
        'timestamp': r.timestamp.isoformat() if r.timestamp else None,
        'soc': r.soc,
        'soh': r.soh,
        'battery_temp': r.battery_temp,
        'motor_temp': r.motor_temp,
        'motor_vibration': r.motor_vibration,
        'brake_pad_wear': r.brake_pad_wear,
        'tire_pressure_fl': r.tire_pressure_fl,
        'tire_pressure_fr': r.tire_pressure_fr,
        'tire_pressure_rl': r.tire_pressure_rl,
        'tire_pressure_rr': r.tire_pressure_rr,
        'distance_traveled': r.distance_traveled
    } for r in readings]
    
    # Get health summary
    health = data_agent.get_vehicle_health_summary(readings_dict)
    
    return health

# ==================== SENSOR DATA ====================

@router.get("/sensor/{vehicle_id}/latest")
async def get_latest_sensor_data(vehicle_id: str, db: Session = Depends(get_db)):
    """Get latest sensor reading"""
    reading = db.query(SensorReading)\
        .filter(SensorReading.vehicle_id == vehicle_id)\
        .order_by(SensorReading.timestamp.desc())\
        .first()
    
    if not reading:
        raise HTTPException(status_code=404, detail="No sensor data found")
    
    return {
        "vehicle_id": reading.vehicle_id,
        "timestamp": reading.timestamp.isoformat(),
        "soc": reading.soc,
        "soh": reading.soh,
        "battery_voltage": reading.battery_voltage,
        "battery_current": reading.battery_current,
        "battery_temp": reading.battery_temp,
        "charge_cycles": reading.charge_cycles,
        "motor_temp": reading.motor_temp,
        "motor_vibration": reading.motor_vibration,
        "motor_torque": reading.motor_torque,
        "motor_rpm": reading.motor_rpm,
        "power_consumption": reading.power_consumption,
        "brake_pad_wear": reading.brake_pad_wear,
        "brake_pressure": reading.brake_pressure,
        "regen_efficiency": reading.regen_efficiency,
        "tire_pressure_fl": reading.tire_pressure_fl,
        "tire_pressure_fr": reading.tire_pressure_fr,
        "tire_pressure_rl": reading.tire_pressure_rl,
        "tire_pressure_rr": reading.tire_pressure_rr,
        "tire_temp_avg": reading.tire_temp_avg,
        "suspension_load": reading.suspension_load,
        "ambient_temp": reading.ambient_temp,
        "ambient_humidity": reading.ambient_humidity,
        "load_weight": reading.load_weight,
        "driving_speed": reading.driving_speed,
        "distance_traveled": reading.distance_traveled,
        "idle_time": reading.idle_time,
        "route_roughness": reading.route_roughness,
        "failure_probability": reading.failure_probability,
        "component_health_score": reading.component_health_score,
        "estimated_rul_hours": reading.estimated_rul_hours
    }

@router.get("/sensor/{vehicle_id}/history")
async def get_sensor_history(
    vehicle_id: str,
    hours: int = Query(24, ge=1, le=168),
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
        .limit(1000)\
        .all()
    
    return [{
        "timestamp": r.timestamp.isoformat(),
        "soc": r.soc,
        "soh": r.soh,
        "battery_temp": r.battery_temp,
        "motor_temp": r.motor_temp,
        "motor_vibration": r.motor_vibration,
        "brake_pad_wear": r.brake_pad_wear,
        "power_consumption": r.power_consumption,
        "driving_speed": r.driving_speed
    } for r in readings]

@router.get("/sensor/{vehicle_id}/analyze")
async def analyze_sensor_data(vehicle_id: str, db: Session = Depends(get_db)):
    """Analyze current sensor data for anomalies"""
    reading = db.query(SensorReading)\
        .filter(SensorReading.vehicle_id == vehicle_id)\
        .order_by(SensorReading.timestamp.desc())\
        .first()
    
    if not reading:
        raise HTTPException(status_code=404, detail="No sensor data found")
    
    # Convert to dict
    reading_dict = {
        'vehicle_id': reading.vehicle_id,
        'timestamp': reading.timestamp.isoformat(),
        'soc': reading.soc,
        'soh': reading.soh,
        'battery_voltage': reading.battery_voltage,
        'battery_current': reading.battery_current,
        'battery_temp': reading.battery_temp,
        'motor_temp': reading.motor_temp,
        'motor_vibration': reading.motor_vibration,
        'motor_torque': reading.motor_torque,
        'brake_pad_wear': reading.brake_pad_wear,
        'brake_pressure': reading.brake_pressure,
        'tire_pressure_fl': reading.tire_pressure_fl,
        'tire_pressure_fr': reading.tire_pressure_fr,
        'tire_pressure_rl': reading.tire_pressure_rl,
        'tire_pressure_rr': reading.tire_pressure_rr,
        'component_health_score': reading.component_health_score,
        'failure_probability': reading.failure_probability
    }
    
    # Analyze with data agent
    analysis = data_agent.analyze_sensor_reading(reading_dict)
    
    # Generate report
    try:
        report = await data_agent.generate_analysis_report(analysis)
        analysis['report'] = report
    except Exception as e:
        analysis['report'] = f"Analysis: {analysis['status']} with {len(analysis['anomalies'])} anomalies detected."
    
    return analysis

# ==================== DIAGNOSIS ====================

@router.post("/diagnosis/{vehicle_id}")
async def diagnose_vehicle(vehicle_id: str, db: Session = Depends(get_db)):
    """Run comprehensive vehicle diagnosis"""
    # Get latest sensor reading
    reading = db.query(SensorReading)\
        .filter(SensorReading.vehicle_id == vehicle_id)\
        .order_by(SensorReading.timestamp.desc())\
        .first()
    
    if not reading:
        raise HTTPException(status_code=404, detail="No sensor data found")
    
    # Convert to dict
    reading_dict = {
        'vehicle_id': reading.vehicle_id,
        'soc': reading.soc,
        'soh': reading.soh,
        'battery_voltage': reading.battery_voltage,
        'battery_current': reading.battery_current,
        'battery_temp': reading.battery_temp,
        'charge_cycles': reading.charge_cycles,
        'motor_temp': reading.motor_temp,
        'motor_vibration': reading.motor_vibration,
        'motor_torque': reading.motor_torque,
        'motor_rpm': reading.motor_rpm,
        'power_consumption': reading.power_consumption,
        'brake_pad_wear': reading.brake_pad_wear,
        'brake_pressure': reading.brake_pressure,
        'regen_efficiency': reading.regen_efficiency,
        'tire_pressure_fl': reading.tire_pressure_fl,
        'tire_pressure_fr': reading.tire_pressure_fr,
        'tire_pressure_rl': reading.tire_pressure_rl,
        'tire_pressure_rr': reading.tire_pressure_rr,
        'distance_traveled': reading.distance_traveled,
        'route_roughness': reading.route_roughness
    }
    
    # Analyze for anomalies
    analysis = data_agent.analyze_sensor_reading(reading_dict)
    
    # Run diagnosis
    diagnosis = diagnosis_agent.diagnose_vehicle(reading_dict, analysis.get('anomalies', []))
    
    # Generate diagnosis report
    try:
        report = await diagnosis_agent.generate_diagnosis_report(diagnosis)
        diagnosis['report'] = report
    except Exception as e:
        diagnosis['report'] = f"Diagnosis: {diagnosis['status']} - {len(diagnosis.get('issues', []))} issues found."
    
    # Get maintenance plan
    if diagnosis.get('issues'):
        try:
            plan = diagnosis_agent.generate_maintenance_plan(diagnosis)
            diagnosis['maintenance_plan'] = plan
        except Exception as e:
            print(f"Maintenance plan error: {e}")
    
    # Create alert if critical
    if any(i.get('severity') == 'Critical' for i in diagnosis.get('issues', [])):
        try:
            alert = Alert(
                vehicle_id=vehicle_id,
                alert_type='Critical Issue',
                severity='Critical',
                component=diagnosis['issues'][0]['component'],
                message=f"Critical issue detected: {diagnosis['issues'][0]['component']}",
                recommendation=diagnosis.get('report', 'Immediate attention required')
            )
            db.add(alert)
            db.commit()
        except Exception as e:
            print(f"Alert creation error: {e}")
    
    return diagnosis

# ==================== CHATBOT ====================

@router.post("/chat/{vehicle_id}", response_model=ChatResponse)
async def chat_with_bot(
    vehicle_id: str,
    message: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    """Chat with vehicle assistant"""
    # Get vehicle data
    reading = db.query(SensorReading)\
        .filter(SensorReading.vehicle_id == vehicle_id)\
        .order_by(SensorReading.timestamp.desc())\
        .first()
    
    vehicle_data = None
    if reading:
        vehicle_data = {
            'vehicle_id': reading.vehicle_id,
            'soc': reading.soc,
            'soh': reading.soh,
            'battery_temp': reading.battery_temp,
            'motor_temp': reading.motor_temp,
            'brake_pad_wear': reading.brake_pad_wear,
            'tire_pressure_fl': reading.tire_pressure_fl,
            'tire_pressure_fr': reading.tire_pressure_fr,
            'tire_pressure_rl': reading.tire_pressure_rl,
            'tire_pressure_rr': reading.tire_pressure_rr,
            'distance_traveled': reading.distance_traveled
        }
    
    # Get diagnosis if needed
    diagnosis = None
    if reading:
        try:
            reading_dict = {k: getattr(reading, k) for k in [
                'soc', 'soh', 'battery_temp', 'motor_temp', 'motor_vibration',
                'brake_pad_wear', 'tire_pressure_fl', 'tire_pressure_fr',
                'tire_pressure_rl', 'tire_pressure_rr'
            ]}
            analysis = data_agent.analyze_sensor_reading(reading_dict)
            if analysis.get('status') == 'Anomaly Detected':
                diagnosis = diagnosis_agent.diagnose_vehicle(reading_dict, analysis.get('anomalies', []))
        except Exception as e:
            print(f"Diagnosis error in chat: {e}")
    
    # Chat
    try:
        response = await chatbot_agent.chat(
            vehicle_id,
            message,
            vehicle_data=vehicle_data,
            diagnosis=diagnosis
        )
        
        return ChatResponse(
            response=response,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

# ==================== APPOINTMENTS ====================

@router.get("/workshops")
async def get_workshops(db: Session = Depends(get_db)):
    """Get all service workshops"""
    workshops = db.query(Workshop).filter(Workshop.is_active == True).all()
    
    return [{
        "workshop_id": w.workshop_id,
        "name": w.name,
        "city": w.city,
        "address": w.address,
        "phone": w.phone,
        "specialties": w.specialties,
        "rating": w.rating,
        "available_slots": w.available_slots,
        "capacity_per_day": w.capacity_per_day,
        "average_wait_days": w.average_wait_days
    } for w in workshops]

@router.post("/appointments/propose/{vehicle_id}")
async def propose_appointment(vehicle_id: str, db: Session = Depends(get_db)):
    """Propose appointment based on diagnosis"""
    # Run diagnosis
    reading = db.query(SensorReading)\
        .filter(SensorReading.vehicle_id == vehicle_id)\
        .order_by(SensorReading.timestamp.desc())\
        .first()
    
    if not reading:
        raise HTTPException(status_code=404, detail="No sensor data found")
    
    # Convert to dict
    reading_dict = {k: getattr(reading, k) for k in [
        'soc', 'soh', 'battery_temp', 'motor_temp', 'motor_vibration',
        'brake_pad_wear', 'brake_pressure', 'tire_pressure_fl'
    ]}
    
    analysis = data_agent.analyze_sensor_reading(reading_dict)
    diagnosis = diagnosis_agent.diagnose_vehicle(reading_dict, analysis.get('anomalies', []))
    
    # Get workshops
    workshops = db.query(Workshop).filter(Workshop.is_active == True).all()
    workshops_dict = [{
        "workshop_id": w.workshop_id,
        "name": w.name,
        "city": w.city,
        "address": w.address,
        "phone": w.phone,
        "specialties": w.specialties,
        "rating": float(w.rating),
        "available_slots": w.available_slots if isinstance(w.available_slots, str) else str(w.available_slots),
        "capacity_per_day": w.capacity_per_day
    } for w in workshops]
    
    # Create proposal
    try:
        proposal = await scheduling_agent.create_appointment_proposal(
            vehicle_id,
            diagnosis,
            workshops_dict
        )
        return proposal
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Appointment proposal error: {str(e)}")

@router.post("/appointments/confirm")
async def confirm_appointment(
    vehicle_id: str = Query(...),
    appointment_data: AppointmentConfirmRequest = None,
    db: Session = Depends(get_db)
):
    """Confirm and book appointment"""
    try:
        # Create appointment dict
        appt_dict = {
            'workshop_id': appointment_data.workshop_id,
            'workshop_name': appointment_data.workshop_name,
            'date': appointment_data.date,
            'time': appointment_data.time,
            'datetime': f"{appointment_data.date} {appointment_data.time}",
            'estimated_duration': appointment_data.estimated_duration,
            'estimated_cost_min': appointment_data.estimated_cost_min,
            'estimated_cost_max': appointment_data.estimated_cost_max
        }
        
        # Confirm with scheduling agent
        appointment = scheduling_agent.confirm_appointment(
            vehicle_id,
            appt_dict,
            appointment_data.notes
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
            estimated_cost=appointment['estimated_cost'][0],
            notes=appointment.get('user_notes')
        )
        db.add(db_appointment)
        db.commit()
        db.refresh(db_appointment)
        
        return {
            "appointment_id": appointment['appointment_id'],
            "confirmation_number": appointment['confirmation_number'],
            "status": "Confirmed",
            "message": "Appointment booked successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Booking error: {str(e)}")

@router.get("/appointments/{vehicle_id}")
async def get_appointments(vehicle_id: str, db: Session = Depends(get_db)):
    """Get vehicle appointments"""
    appointments = db.query(Appointment)\
        .filter(Appointment.vehicle_id == vehicle_id)\
        .order_by(Appointment.scheduled_date.desc())\
        .all()
    
    return [{
        "appointment_id": a.appointment_id,
        "vehicle_id": a.vehicle_id,
        "workshop_id": a.workshop_id,
        "scheduled_date": a.scheduled_date.isoformat(),
        "estimated_duration_hours": a.estimated_duration_hours,
        "service_type": a.service_type,
        "status": a.status,
        "priority": a.priority,
        "estimated_cost": a.estimated_cost,
        "notes": a.notes
    } for a in appointments]

# ==================== MAINTENANCE ====================

@router.get("/maintenance/{vehicle_id}")
async def get_maintenance_history(vehicle_id: str, db: Session = Depends(get_db)):
    """Get maintenance history"""
    records = db.query(MaintenanceRecord)\
        .filter(MaintenanceRecord.vehicle_id == vehicle_id)\
        .order_by(MaintenanceRecord.maintenance_date.desc())\
        .all()
    
    return [{
        "maintenance_id": r.maintenance_id,
        "vehicle_id": r.vehicle_id,
        "detection_date": r.detection_date.isoformat(),
        "maintenance_date": r.maintenance_date.isoformat(),
        "component": r.component,
        "issue_detected": r.issue_detected,
        "maintenance_type": r.maintenance_type,
        "repair_duration_hours": r.repair_duration_hours,
        "cost_usd": r.cost_usd,
        "parts_replaced": r.parts_replaced,
        "workshop_id": r.workshop_id,
        "severity": r.severity,
        "downtime_hours": r.downtime_hours,
        "description": r.description,
        "status": r.status
    } for r in records]

# ==================== FEEDBACK ====================

@router.post("/feedback")
async def submit_feedback(feedback_data: FeedbackRequest, db: Session = Depends(get_db)):
    """Submit feedback on repair"""
    try:
        # Process feedback with agent
        processed = await feedback_agent.process_feedback({
            'vehicle_id': feedback_data.vehicle_id,
            'maintenance_id': feedback_data.maintenance_id,
            'rating': feedback_data.rating,
            'comment': feedback_data.comment,
            'repair_effectiveness': feedback_data.repair_effectiveness,
            'service_quality': feedback_data.service_quality,
            'communication_rating': feedback_data.communication_rating
        })
        
        # Save to database
        feedback_id = f"FBK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        db_feedback = Feedback(
            feedback_id=feedback_id,
            vehicle_id=feedback_data.vehicle_id,
            maintenance_id=feedback_data.maintenance_id,
            rating=feedback_data.rating,
            sentiment=processed.get('sentiment', 'Neutral'),
            comment=feedback_data.comment,
            repair_effectiveness=feedback_data.repair_effectiveness,
            service_quality=feedback_data.service_quality,
            communication_rating=feedback_data.communication_rating
        )
        db.add(db_feedback)
        db.commit()
        
        # Share with manufacturer if needed
        if processed.get('share_with_manufacturer'):
            try:
                await quality_agent.process_feedback(feedback_data.dict())
            except Exception as e:
                print(f"Quality insights error: {e}")
        
        return {
            "status": "success",
            "feedback_id": feedback_id,
            "processed": processed
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Feedback error: {str(e)}")

# ==================== QUALITY INSIGHTS ====================

@router.get("/insights")
async def get_quality_insights(db: Session = Depends(get_db)):
    """Get quality insights for manufacturer"""
    # Get recent maintenance records
    records = db.query(MaintenanceRecord)\
        .order_by(MaintenanceRecord.maintenance_date.desc())\
        .limit(200)\
        .all()
    
    records_dict = [{
        'component': r.component,
        'issue_detected': r.issue_detected,
        'cost_usd': r.cost_usd,
        'severity': r.severity,
        'maintenance_type': r.maintenance_type
    } for r in records]
    
    # Analyze patterns
    try:
        insights = await quality_agent.generate_insights(records_dict)
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insights error: {str(e)}")
