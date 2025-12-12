"""
SQLAlchemy ORM Models for TorqCare Database
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Vehicle(Base):
    __tablename__ = "vehicles"
    
    vehicle_id = Column(String(20), primary_key=True)
    model = Column(String(100), default="Tesla Model 3")
    year = Column(Integer, default=2023)
    vin = Column(String(17), unique=True)
    owner_name = Column(String(100))
    owner_email = Column(String(100))
    owner_phone = Column(String(20))
    registration_date = Column(DateTime, default=datetime.utcnow)
    last_service_date = Column(DateTime)
    total_distance_km = Column(Float, default=0.0)
    status = Column(String(20), default="Active")
    
    # Relationships
    sensor_readings = relationship("SensorReading", back_populates="vehicle")
    maintenance_records = relationship("MaintenanceRecord", back_populates="vehicle")
    appointments = relationship("Appointment", back_populates="vehicle")
    feedback_records = relationship("Feedback", back_populates="vehicle")

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String(20), ForeignKey("vehicles.vehicle_id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Battery System
    soc = Column(Float)  # State of Charge
    soh = Column(Float)  # State of Health
    battery_voltage = Column(Float)
    battery_current = Column(Float)
    battery_temp = Column(Float)
    charge_cycles = Column(Integer)
    
    # Electric Motor
    motor_temp = Column(Float)
    motor_vibration = Column(Float)
    motor_torque = Column(Float)
    motor_rpm = Column(Float)
    power_consumption = Column(Float)
    
    # Brake System
    brake_pad_wear = Column(Float)
    brake_pressure = Column(Float)
    regen_efficiency = Column(Float)
    
    # Tires
    tire_pressure_fl = Column(Float)
    tire_pressure_fr = Column(Float)
    tire_pressure_rl = Column(Float)
    tire_pressure_rr = Column(Float)
    tire_temp_avg = Column(Float)
    
    # Suspension
    suspension_load = Column(Float)
    
    # Environmental
    ambient_temp = Column(Float)
    ambient_humidity = Column(Float)
    load_weight = Column(Float)
    driving_speed = Column(Float)
    
    # Telematics
    distance_traveled = Column(Float)
    idle_time = Column(Integer)
    route_roughness = Column(Integer)
    
    # Predictive Analytics
    failure_probability = Column(Float)
    component_health_score = Column(Float)
    estimated_rul_hours = Column(Float)
    
    # Relationship
    vehicle = relationship("Vehicle", back_populates="sensor_readings")

class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"
    
    maintenance_id = Column(String(20), primary_key=True)
    vehicle_id = Column(String(20), ForeignKey("vehicles.vehicle_id"), nullable=False)
    detection_date = Column(DateTime, nullable=False)
    maintenance_date = Column(DateTime, nullable=False)
    completion_date = Column(DateTime)
    
    component = Column(String(50), nullable=False)
    issue_detected = Column(String(200), nullable=False)
    maintenance_type = Column(String(50))  # Preventive, Corrective, Predictive
    
    repair_duration_hours = Column(Float)
    cost_usd = Column(Float)
    parts_replaced = Column(Boolean, default=False)
    
    workshop_id = Column(String(20), ForeignKey("workshops.workshop_id"))
    technician_id = Column(String(20))
    
    severity = Column(String(20))  # Low, Medium, High, Critical
    downtime_hours = Column(Float)
    odometer_reading = Column(Float)
    description = Column(Text)
    
    status = Column(String(20), default="Pending")  # Pending, In Progress, Completed
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="maintenance_records")
    workshop = relationship("Workshop", back_populates="maintenance_records")
    feedback = relationship("Feedback", back_populates="maintenance_record")

class Appointment(Base):
    __tablename__ = "appointments"
    
    appointment_id = Column(String(20), primary_key=True)
    vehicle_id = Column(String(20), ForeignKey("vehicles.vehicle_id"), nullable=False)
    workshop_id = Column(String(20), ForeignKey("workshops.workshop_id"), nullable=False)
    
    scheduled_date = Column(DateTime, nullable=False)
    estimated_duration_hours = Column(Float)
    service_type = Column(String(100))
    
    status = Column(String(20), default="Scheduled")  # Scheduled, Confirmed, Completed, Cancelled
    created_date = Column(DateTime, default=datetime.utcnow)
    confirmed_date = Column(DateTime)
    
    priority = Column(String(20), default="Medium")
    estimated_cost = Column(Float)
    
    notes = Column(Text)
    cancellation_reason = Column(Text)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="appointments")
    workshop = relationship("Workshop", back_populates="appointments")

class Workshop(Base):
    __tablename__ = "workshops"
    
    workshop_id = Column(String(20), primary_key=True)
    name = Column(String(200), nullable=False)
    city = Column(String(100))
    address = Column(String(300))
    phone = Column(String(20))
    email = Column(String(100))
    
    specialties = Column(Text)
    rating = Column(Float, default=5.0)
    
    available_slots = Column(JSON)  # JSON structure with date and time slots
    capacity_per_day = Column(Integer, default=10)
    average_wait_days = Column(Integer, default=2)
    
    is_active = Column(Boolean, default=True)
    
    # Relationships
    appointments = relationship("Appointment", back_populates="workshop")
    maintenance_records = relationship("MaintenanceRecord", back_populates="workshop")

class Feedback(Base):
    __tablename__ = "feedback"
    
    feedback_id = Column(String(20), primary_key=True)
    maintenance_id = Column(String(20), ForeignKey("maintenance_records.maintenance_id"))
    vehicle_id = Column(String(20), ForeignKey("vehicles.vehicle_id"), nullable=False)
    
    feedback_date = Column(DateTime, default=datetime.utcnow)
    rating = Column(Integer)  # 1-5 stars
    sentiment = Column(String(20))  # Positive, Neutral, Negative
    comment = Column(Text)
    
    repair_effectiveness = Column(Integer)  # 1-5
    service_quality = Column(Integer)  # 1-5
    communication_rating = Column(Integer)  # 1-5
    would_recommend = Column(Boolean, default=True)
    
    # Relationships
    maintenance_record = relationship("MaintenanceRecord", back_populates="feedback")
    vehicle = relationship("Vehicle", back_populates="feedback_records")

class Alert(Base):
    __tablename__ = "alerts"
    
    alert_id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String(20), ForeignKey("vehicles.vehicle_id"), nullable=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    alert_type = Column(String(50))  # Failure Prediction, Maintenance Due, Critical Issue
    severity = Column(String(20))  # Low, Medium, High, Critical
    
    component = Column(String(50))
    message = Column(Text)
    recommendation = Column(Text)
    
    is_acknowledged = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    resolved_date = Column(DateTime)
    
    predicted_failure_date = Column(DateTime)
    confidence_score = Column(Float)

class QualityInsight(Base):
    __tablename__ = "quality_insights"
    
    insight_id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    component = Column(String(50), nullable=False)
    issue_pattern = Column(String(200))
    affected_vehicles_count = Column(Integer)
    affected_vehicle_ids = Column(JSON)
    
    frequency = Column(Integer)  # Number of occurrences
    avg_failure_age_km = Column(Float)
    avg_repair_cost = Column(Float)
    
    root_cause_analysis = Column(Text)
    recommendation_to_manufacturer = Column(Text)
    
    severity_trend = Column(String(20))  # Increasing, Stable, Decreasing
    priority = Column(String(20))  # Low, Medium, High, Critical
    
    status = Column(String(20), default="Open")  # Open, Under Investigation, Resolved
