"""
TorqCare Database Connection and SQLAlchemy Models
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON, Text, Date, ForeignKey, Interval
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database configuration
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://torqcare_user:your_password@localhost:5432/torqcare_db'
)

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# ===============================================
# SQLAlchemy Models
# ===============================================

class Vehicle(Base):
    __tablename__ = 'vehicles'
    
    vehicle_id = Column(String(50), primary_key=True)
    vin = Column(String(17), unique=True, nullable=False)
    make = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    color = Column(String(30))
    owner_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    registration_date = Column(Date)
    engine_type = Column(String(50))
    engine_capacity = Column(Float)
    transmission_type = Column(String(30))
    current_mileage = Column(Float)
    last_service_date = Column(Date)
    next_service_due = Column(Date)
    health_score = Column(Float, default=100.0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    owner = relationship("User", back_populates="vehicles")
    sensor_data = relationship("SensorData", back_populates="vehicle", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="vehicle", cascade="all, delete-orphan")
    maintenance_history = relationship("MaintenanceHistory", back_populates="vehicle", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    address = Column(Text)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    notification_preferences = Column(JSON)
    preferred_workshop_id = Column(Integer)
    
    # Relationships
    vehicles = relationship("Vehicle", back_populates="owner")


class SensorData(Base):
    __tablename__ = 'sensor_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String(50), ForeignKey('vehicles.vehicle_id', ondelete='CASCADE'), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.now)
    
    # Engine metrics
    engine_temp = Column(Float)
    rpm = Column(Float)
    oil_pressure = Column(Float)
    coolant_level = Column(Float)
    
    # Electrical system
    battery_voltage = Column(Float)
    alternator_voltage = Column(Float)
    
    # Fuel system
    fuel_level = Column(Float)
    fuel_pressure = Column(Float)
    
    # Tire monitoring
    tire_pressure_fl = Column(Float)
    tire_pressure_fr = Column(Float)
    tire_pressure_rl = Column(Float)
    tire_pressure_rr = Column(Float)
    tire_temp_fl = Column(Float)
    tire_temp_fr = Column(Float)
    tire_temp_rl = Column(Float)
    tire_temp_rr = Column(Float)
    
    # Brake system
    brake_fluid_level = Column(Float)
    brake_pad_thickness_fl = Column(Float)
    brake_pad_thickness_fr = Column(Float)
    brake_pad_thickness_rl = Column(Float)
    brake_pad_thickness_rr = Column(Float)
    
    # Transmission
    transmission_temp = Column(Float)
    transmission_fluid_level = Column(Float)
    
    # Performance
    speed = Column(Float)
    acceleration = Column(Float)
    odometer = Column(Float)
    
    # Environmental
    ambient_temp = Column(Float)
    cabin_temp = Column(Float)
    
    # GPS
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Anomaly flags
    anomaly_detected = Column(Boolean, default=False)
    anomaly_type = Column(String(100))
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="sensor_data")


class MaintenanceHistory(Base):
    __tablename__ = 'maintenance_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String(50), ForeignKey('vehicles.vehicle_id', ondelete='CASCADE'), nullable=False)
    service_date = Column(DateTime, nullable=False)
    service_type = Column(String(50), nullable=False)
    description = Column(Text)
    mileage_at_service = Column(Float)
    workshop_id = Column(Integer, ForeignKey('workshops.workshop_id', ondelete='SET NULL'))
    mechanic_name = Column(String(100))
    parts_replaced = Column(JSON)
    labor_hours = Column(Float)
    parts_cost = Column(Float)
    labor_cost = Column(Float)
    total_cost = Column(Float)
    issue_reported = Column(Text)
    issue_resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text)
    customer_rating = Column(Integer)
    manufacturer_notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="maintenance_history")
    workshop = relationship("Workshop", back_populates="maintenance_records")


class Appointment(Base):
    __tablename__ = 'appointments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String(50), ForeignKey('vehicles.vehicle_id', ondelete='CASCADE'), nullable=False)
    issue_type = Column(String(100), nullable=False)
    urgency = Column(String(20), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    requested_date = Column(Date)
    scheduled_time = Column(DateTime)
    completed_time = Column(DateTime)
    workshop_id = Column(Integer, ForeignKey('workshops.workshop_id', ondelete='SET NULL'))
    assigned_mechanic = Column(String(100))
    estimated_duration = Column(Interval)
    estimated_cost = Column(Float)
    status = Column(String(20), nullable=False, default='pending')
    suggested_slots = Column(JSON)
    auto_scheduled = Column(Boolean, default=False)
    customer_accepted = Column(Boolean)
    cancellation_reason = Column(Text)
    predicted_issue = Column(String(100))
    prediction_confidence = Column(Float)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="appointments")
    workshop = relationship("Workshop", back_populates="appointments")
    feedback = relationship("Feedback", back_populates="appointment", uselist=False)


class Workshop(Base):
    __tablename__ = 'workshops'
    
    workshop_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    address = Column(Text, nullable=False)
    city = Column(String(50))
    state = Column(String(50))
    zip_code = Column(String(10))
    phone = Column(String(20))
    email = Column(String(100))
    website = Column(String(200))
    latitude = Column(Float)
    longitude = Column(Float)
    specializations = Column(JSON)
    certified_brands = Column(JSON)
    equipment_available = Column(JSON)
    operating_hours = Column(JSON)
    appointment_slots_per_hour = Column(Integer, default=2)
    average_rating = Column(Float)
    total_services_completed = Column(Integer, default=0)
    average_completion_time = Column(Interval)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    appointments = relationship("Appointment", back_populates="workshop")
    maintenance_records = relationship("MaintenanceHistory", back_populates="workshop")


class Feedback(Base):
    __tablename__ = 'feedback'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String(50), ForeignKey('vehicles.vehicle_id', ondelete='CASCADE'), nullable=False)
    appointment_id = Column(Integer, ForeignKey('appointments.id', ondelete='SET NULL'))
    feedback_type = Column(String(20), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    repair_quality_rating = Column(Integer)
    service_speed_rating = Column(Integer)
    cost_satisfaction_rating = Column(Integer)
    issue_recurring = Column(Boolean, default=False)
    issue_fully_resolved = Column(Boolean)
    additional_issues_found = Column(Text)
    shared_with_manufacturer = Column(Boolean, default=False)
    shared_with_workshop = Column(Boolean, default=False)
    manufacturer_response = Column(Text)
    workshop_response = Column(Text)
    photos = Column(JSON)
    submitted_at = Column(DateTime, default=datetime.now)
    processed_at = Column(DateTime)
    
    # Relationships
    appointment = relationship("Appointment", back_populates="feedback")


class Prediction(Base):
    __tablename__ = 'predictions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String(50), ForeignKey('vehicles.vehicle_id', ondelete='CASCADE'), nullable=False)
    predicted_failure = Column(String(100), nullable=False)
    prediction_model = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=False)
    predicted_at = Column(DateTime, default=datetime.now)
    estimated_failure_date = Column(Date)
    time_to_failure_days = Column(Integer)
    contributing_metrics = Column(JSON)
    historical_patterns = Column(JSON)
    severity = Column(String(20))
    recommended_action = Column(Text)
    estimated_repair_cost = Column(Float)
    actual_failure_occurred = Column(Boolean)
    actual_failure_date = Column(Date)
    prediction_accuracy = Column(Float)
    status = Column(String(20), default='active')
    resolution_notes = Column(Text)


class Alert(Base):
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String(50), ForeignKey('vehicles.vehicle_id', ondelete='CASCADE'), nullable=False)
    alert_type = Column(String(50), nullable=False)
    alert_category = Column(String(50))
    message = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)
    triggered_by = Column(String(50))
    sensor_reading_id = Column(Integer, ForeignKey('sensor_data.id', ondelete='SET NULL'))
    prediction_id = Column(Integer, ForeignKey('predictions.id', ondelete='SET NULL'))
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)
    action_required = Column(Boolean, default=False)
    action_taken = Column(String(100))
    appointment_created = Column(Integer, ForeignKey('appointments.id', ondelete='SET NULL'))
    created_at = Column(DateTime, default=datetime.now)


class AgentLog(Base):
    __tablename__ = 'agent_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String(50), nullable=False)
    vehicle_id = Column(String(50))
    action_type = Column(String(50), nullable=False)
    input_data = Column(JSON)
    output_data = Column(JSON)
    execution_time_ms = Column(Integer)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    triggered_by = Column(String(50))
    related_entities = Column(JSON)
    logged_at = Column(DateTime, default=datetime.now)


# ===============================================
# Database Helper Functions
# ===============================================

def get_db_session():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """Initialize database with tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")


def seed_sample_data():
    """Seed database with sample data for testing"""
    db = SessionLocal()
    
    try:
        # Create sample user
        user = User(
            email='john.doe@example.com',
            full_name='John Doe',
            phone='+1234567890',
            password_hash='hashed_password_placeholder'
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create sample vehicle
        vehicle = Vehicle(
            vehicle_id='VEH001',
            vin='5YJ3E1EA7KF123456',
            make='Tesla',
            model='Model 3',
            year=2023,
            owner_id=user.user_id,
            engine_type='Electric',
            current_mileage=15234.50,
            health_score=95.0
        )
        db.add(vehicle)
        db.commit()
        
        # Create sample workshops
        workshops_data = [
            {'name': 'AutoCare Center', 'city': 'San Francisco', 'phone': '+1-415-555-0100', 'average_rating': 4.8},
            {'name': 'Premium Motors', 'city': 'San Francisco', 'phone': '+1-415-555-0200', 'average_rating': 4.6},
            {'name': 'QuickFix Garage', 'city': 'San Francisco', 'phone': '+1-415-555-0300', 'average_rating': 4.9}
        ]
        
        for workshop_data in workshops_data:
            workshop = Workshop(
                name=workshop_data['name'],
                address='123 Main St',
                city=workshop_data['city'],
                state='CA',
                phone=workshop_data['phone'],
                average_rating=workshop_data['average_rating'],
                is_active=True
            )
            db.add(workshop)
        
        db.commit()
        print("✅ Sample data seeded successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding data: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing TorqCare database...")
    init_database()
    seed_sample_data()
    print("Database setup complete!")