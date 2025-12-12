"""
Configuration management for TorqCare
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Database
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://torqcare_user:torqcare_pass@localhost:5432/torqcare_db"
    )
    
    # ML Models
    ML_MODEL_PATH = "ml_models/trained_models"
    
    # Data paths
    DATA_DIR = "backend/data"
    
    # Agent settings
    AGENT_TEMPERATURE = 0.3
    AGENT_MODEL = "llama-3.1-70b-versatile"
    
    # Monitoring
    SENSOR_UPDATE_INTERVAL = 10  # seconds
    HEALTH_CHECK_INTERVAL = 30  # seconds
    
    # Thresholds
    CRITICAL_BATTERY_TEMP = 60  # Celsius
    MIN_BRAKE_PAD_WEAR = 2  # mm
    MIN_TIRE_PRESSURE = 28  # PSI
    MIN_SOC = 20  # percent
    MIN_SOH = 75  # percent

config = Config()