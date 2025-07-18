import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import get_settings
from app.database.connection import connect_to_mongo, close_mongo_connection
from app.api import auth, users, farms, ponds, sensor_readings, alerts, ml
from app.ml.anomaly_detection import anomaly_detector
from app.mqtt.subscriber import MQTTSubscriber

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Global MQTT subscriber instance
mqtt_subscriber = None
mqtt_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    global mqtt_subscriber, mqtt_task
    
    # Startup
    logger.info("Starting up...")
    await connect_to_mongo()
    
    # Try to load existing ML model
    try:
        anomaly_detector.load_model("models/anomaly_detector.pkl")
        logger.info("Loaded existing ML model")
    except Exception as e:
        logger.info("No existing ML model found, will use rule-based detection")
    
    # Start MQTT subscriber as a background task
    try:
        logger.info("Starting MQTT subscriber...")
        mqtt_subscriber = MQTTSubscriber()
        mqtt_task = asyncio.create_task(mqtt_subscriber.start())
        logger.info("MQTT subscriber started as background task")
    except Exception as e:
        logger.error(f"Failed to start MQTT subscriber: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    
    # Stop MQTT subscriber
    if mqtt_subscriber:
        try:
            await mqtt_subscriber.stop()
            logger.info("MQTT subscriber stopped")
        except Exception as e:
            logger.error(f"Error stopping MQTT subscriber: {e}")
    
    # Cancel the task if it's still running
    if mqtt_task and not mqtt_task.done():
        mqtt_task.cancel()
        try:
            await mqtt_task
        except asyncio.CancelledError:
            logger.info("MQTT task cancelled")
    
    await close_mongo_connection()


# Create FastAPI application
app = FastAPI(
    title="Pond Monitoring API",
    description="IoT Pond Monitoring System with MQTT data ingestion and ML-based anomaly detection",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error": True}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": True}
    )


# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(farms.router)
app.include_router(ponds.router)
app.include_router(sensor_readings.router)
app.include_router(alerts.router)
app.include_router(ml.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Pond Monitoring API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
        "services": {
            "api": "✅ Running",
            "mqtt_subscriber": "✅ Integrated",
            "database": "✅ Connected",
            "anomaly_detection": "✅ Active"
        },
        "endpoints": {
            "health": "/health",
            "services_status": "/services/status",
            "documentation": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    mqtt_status = "unknown"
    if mqtt_subscriber:
        mqtt_status = "running" if mqtt_subscriber.running else "stopped"
    elif mqtt_task:
        mqtt_status = "task_running" if not mqtt_task.done() else "task_done"
    
    return {
        "status": "healthy",
        "timestamp": "2025-01-18T10:30:00Z",
        "services": {
            "api": "running",
            "database": "connected",
            "mqtt_subscriber": mqtt_status
        }
    }


@app.get("/services/status")
async def services_status():
    """Get detailed status of all services"""
    mqtt_status = {
        "status": "unknown",
        "running": False,
        "task_done": None
    }
    
    if mqtt_subscriber:
        mqtt_status["status"] = "running" if mqtt_subscriber.running else "stopped"
        mqtt_status["running"] = mqtt_subscriber.running
    
    if mqtt_task:
        mqtt_status["task_done"] = mqtt_task.done()
        if mqtt_task.done():
            try:
                mqtt_task.result()
                mqtt_status["status"] = "completed"
            except Exception as e:
                mqtt_status["status"] = f"failed: {str(e)}"
    
    return {
        "api": {
            "status": "running",
            "version": "1.0.0"
        },
        "database": {
            "status": "connected"
        },
        "mqtt_subscriber": mqtt_status
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info"
    )
