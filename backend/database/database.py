"""
Database configuration and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://torqcare_user:torqcare_pass@localhost:5432/torqcare_db"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency for FastAPI
def get_db():
    """Get database session for FastAPI dependency injection"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """Context manager for database session"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    from .models import Base
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")

def load_csv_data_to_db():
    """Load CSV data into PostgreSQL database"""
    import pandas as pd
    from .models import (
        Vehicle, SensorReading, MaintenanceRecord, 
        Appointment, Workshop, Feedback
    )
    from datetime import datetime
    
    print("Loading CSV data into database...")
    
    with get_db_context() as db:
        # Load Workshops
        print("Loading workshops...")
        workshops_df = pd.read_csv("backend/data/workshops.csv")
        for _, row in workshops_df.iterrows():
            workshop = Workshop(
                workshop_id=row['workshop_id'],
                name=row['name'],
                city=row['city'],
                address=row['address'],
                phone=row['phone'],
                specialties=row['specialties'],
                rating=float(row['rating']),
                available_slots=eval(row['available_slots']),
                capacity_per_day=int(row['capacity_per_day']),
                average_wait_days=int(row['average_wait_days'])
            )
            db.merge(workshop)
        db.commit()
        print(f"✓ Loaded {len(workshops_df)} workshops")
        
        # Load Vehicles
        print("Loading vehicles...")
        sensor_df = pd.read_csv("backend/data/sensor_data.csv")
        vehicle_ids = sensor_df['vehicle_id'].unique()
        
        for i, vehicle_id in enumerate(vehicle_ids):
            vehicle = Vehicle(
                vehicle_id=vehicle_id,
                model="Tesla Model 3",
                year=2023,
                vin=f"5YJ3E1EA{i:09d}",
                owner_name=f"Owner {vehicle_id}",
                owner_email=f"owner{vehicle_id}@torqcare.com",
                owner_phone=f"+1-555-{i:07d}",
                status="Active"
            )
            db.merge(vehicle)
        db.commit()
        print(f"✓ Loaded {len(vehicle_ids)} vehicles")
        
        # Load Sensor Readings (load in batches for performance)
        print("Loading sensor readings...")
        batch_size = 1000
        for i in range(0, len(sensor_df), batch_size):
            batch = sensor_df.iloc[i:i+batch_size]
            for _, row in batch.iterrows():
                reading = SensorReading(
                    vehicle_id=row['vehicle_id'],
                    timestamp=pd.to_datetime(row['timestamp']),
                    soc=float(row['soc']),
                    soh=float(row['soh']),
                    battery_voltage=float(row['battery_voltage']),
                    battery_current=float(row['battery_current']),
                    battery_temp=float(row['battery_temp']),
                    charge_cycles=int(row['charge_cycles']),
                    motor_temp=float(row['motor_temp']),
                    motor_vibration=float(row['motor_vibration']),
                    motor_torque=float(row['motor_torque']),
                    motor_rpm=float(row['motor_rpm']),
                    power_consumption=float(row['power_consumption']),
                    brake_pad_wear=float(row['brake_pad_wear']),
                    brake_pressure=float(row['brake_pressure']),
                    regen_efficiency=float(row['regen_efficiency']),
                    tire_pressure_fl=float(row['tire_pressure_fl']),
                    tire_pressure_fr=float(row['tire_pressure_fr']),
                    tire_pressure_rl=float(row['tire_pressure_rl']),
                    tire_pressure_rr=float(row['tire_pressure_rr']),
                    tire_temp_avg=float(row['tire_temp_avg']),
                    suspension_load=float(row['suspension_load']),
                    ambient_temp=float(row['ambient_temp']),
                    ambient_humidity=float(row['ambient_humidity']),
                    load_weight=float(row['load_weight']),
                    driving_speed=float(row['driving_speed']),
                    distance_traveled=float(row['distance_traveled']),
                    idle_time=int(row['idle_time']),
                    route_roughness=int(row['route_roughness']),
                    failure_probability=float(row['failure_probability']),
                    component_health_score=float(row['component_health_score']),
                    estimated_rul_hours=float(row['estimated_rul_hours'])
                )
                db.add(reading)
            db.commit()
            print(f"  Loaded batch {i//batch_size + 1}/{(len(sensor_df)-1)//batch_size + 1}")
        print(f"✓ Loaded {len(sensor_df)} sensor readings")
        
        # Load Maintenance Records
        print("Loading maintenance records...")
        maintenance_df = pd.read_csv("backend/data/maintenance_history.csv")
        for _, row in maintenance_df.iterrows():
            record = MaintenanceRecord(
                maintenance_id=row['maintenance_id'],
                vehicle_id=row['vehicle_id'],
                detection_date=pd.to_datetime(row['detection_date']),
                maintenance_date=pd.to_datetime(row['maintenance_date']),
                component=row['component'],
                issue_detected=row['issue_detected'],
                maintenance_type=row['maintenance_type'],
                repair_duration_hours=float(row['repair_duration_hours']),
                cost_usd=float(row['cost_usd']),
                parts_replaced=bool(row['parts_replaced']),
                workshop_id=row['workshop_id'],
                technician_id=row['technician_id'],
                severity=row['severity'],
                downtime_hours=float(row['downtime_hours']),
                odometer_reading=float(row['odometer_reading']),
                description=row['description'],
                status="Completed"
            )
            db.merge(record)
        db.commit()
        print(f"✓ Loaded {len(maintenance_df)} maintenance records")
        
        # Load Appointments
        print("Loading appointments...")
        appointments_df = pd.read_csv("backend/data/appointments.csv")
        for _, row in appointments_df.iterrows():
            appointment = Appointment(
                appointment_id=row['appointment_id'],
                vehicle_id=row['vehicle_id'],
                workshop_id=row['workshop_id'],
                scheduled_date=pd.to_datetime(row['scheduled_date']),
                estimated_duration_hours=float(row['estimated_duration_hours']),
                service_type=row['service_type'],
                status=row['status'],
                created_date=pd.to_datetime(row['created_date']),
                priority=row['priority'],
                estimated_cost=float(row['estimated_cost'])
            )
            db.merge(appointment)
        db.commit()
        print(f"✓ Loaded {len(appointments_df)} appointments")
        
        # Load Feedback
        print("Loading feedback...")
        feedback_df = pd.read_csv("backend/data/feedback.csv")
        for _, row in feedback_df.iterrows():
            feedback = Feedback(
                feedback_id=row['feedback_id'],
                maintenance_id=row['maintenance_id'],
                vehicle_id=row['vehicle_id'],
                feedback_date=pd.to_datetime(row['feedback_date']),
                rating=int(row['rating']),
                sentiment=row['sentiment'],
                comment=row['comment'],
                repair_effectiveness=int(row['repair_effectiveness']),
                service_quality=int(row['service_quality']),
                communication_rating=int(row['communication_rating']),
                would_recommend=bool(row['would_recommend'])
            )
            db.merge(feedback)
        db.commit()
        print(f"✓ Loaded {len(feedback_df)} feedback records")
    
    print("\n✅ All CSV data loaded into PostgreSQL successfully!")

if __name__ == "__main__":
    init_db()
    load_csv_data_to_db()
