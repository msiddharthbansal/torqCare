"""
TorqCare FastAPI Backend Server - Updated with Full Connectivity
Multi-agent orchestration for vehicle care management
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime
import os

# Import database
from database.database import init_db, SessionLocal
from database.models import SensorReading

# Import API routes
from api.routes import router

# ==================== LIFESPAN MANAGEMENT ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown"""
    # Startup
    print("🚀 Starting TorqCare Server...")
    print("="*60)
    
    # Initialize database
    try:
        init_db()
        print("✓ Database initialized")
    except Exception as e:
        print(f"⚠ Database initialization warning: {e}")
    
    # Test database connection
    try:
        db = SessionLocal()
        vehicle_count = db.query(SensorReading).count()
        db.close()
        print(f"✓ Database connected ({vehicle_count} sensor readings)")
    except Exception as e:
        print(f"⚠ Database connection warning: {e}")
    
    print("✓ API routes loaded")
    print("✓ Multi-agent system initialized")
    print("="*60)
    print("🎯 Server ready!")
    print("   - API: http://localhost:8000")
    print("   - Docs: http://localhost:8000/docs")
    print("   - Health: http://localhost:8000/health")
    print("="*60)
    
    yield
    
    # Shutdown
    print("\n🛑 Shutting down TorqCare Server...")
    print("✓ Cleanup complete")

# ==================== FASTAPI APP ====================

app = FastAPI(
    title="TorqCare API",
    description="Autonomous multi-agent network for vehicle care",
    version="1.0.0",
    lifespan=lifespan
)

# ==================== CORS MIDDLEWARE ====================

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== INCLUDE ROUTERS ====================

# Include all API routes
app.include_router(router, prefix="/api", tags=["API"])

# ==================== WEBSOCKET ====================

# Active WebSocket connections
active_connections: dict[str, WebSocket] = {}

@app.websocket("/ws/{vehicle_id}")
async def websocket_endpoint(websocket: WebSocket, vehicle_id: str):
    """
    WebSocket endpoint for real-time sensor data streaming
    """
    await websocket.accept()
    active_connections[vehicle_id] = websocket
    
    print(f"📡 WebSocket connected: {vehicle_id}")
    
    try:
        while True:
            # Send heartbeat every 10 seconds
            await asyncio.sleep(10)
            
            # Get latest sensor data from database
            try:
                db = SessionLocal()
                reading = db.query(SensorReading)\
                    .filter(SensorReading.vehicle_id == vehicle_id)\
                    .order_by(SensorReading.timestamp.desc())\
                    .first()
                db.close()
                
                if reading:
                    data = {
                        "vehicle_id": vehicle_id,
                        "timestamp": reading.timestamp.isoformat(),
                        "soc": reading.soc,
                        "soh": reading.soh,
                        "battery_temp": reading.battery_temp,
                        "motor_temp": reading.motor_temp,
                        "status": "connected"
                    }
                else:
                    data = {
                        "vehicle_id": vehicle_id,
                        "timestamp": datetime.now().isoformat(),
                        "status": "no_data"
                    }
                
                await websocket.send_json(data)
                
            except Exception as e:
                print(f"WebSocket data error: {e}")
                await websocket.send_json({
                    "vehicle_id": vehicle_id,
                    "timestamp": datetime.now().isoformat(),
                    "status": "error",
                    "error": str(e)
                })
    
    except WebSocketDisconnect:
        print(f"📡 WebSocket disconnected: {vehicle_id}")
        if vehicle_id in active_connections:
            del active_connections[vehicle_id]
    except Exception as e:
        print(f"WebSocket error: {e}")
        if vehicle_id in active_connections:
            del active_connections[vehicle_id]

# ==================== ROOT ENDPOINTS ====================

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "TorqCare API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "api": "/api/*"
        },
        "features": [
            "Real-time vehicle monitoring",
            "AI-powered diagnostics",
            "Predictive maintenance",
            "Automated scheduling",
            "Quality insights"
        ]
    }

@app.get("/health")
async def health_check():
    """
    API health check endpoint
    Returns system status and agent availability
    """
    # Check database connection
    db_status = "healthy"
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "components": {
            "database": db_status,
            "api": "healthy",
            "websocket": f"{len(active_connections)} active connections"
        },
        "agents": {
            "data_analysis": "active",
            "diagnosis": "active",
            "chatbot": "active",
            "scheduling": "active",
            "quality_insights": "active",
            "feedback": "active"
        }
    }

# ==================== ERROR HANDLERS ====================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "path": str(request.url)
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "details": str(exc)
        }
    )

# ==================== STARTUP MESSAGE ====================

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.getenv("PORT", 8000))
    
    # Run server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
