import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import get_settings
from app.database.connection import connect_to_mongo, close_mongo_connection
from app.api import auth, users, farms, ponds, sensor_readings, alerts, ml
from app.ml.anomaly_detection import anomaly_detector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    # Startup
    logger.info("Starting up...")
    await connect_to_mongo()
    
    # Try to load existing ML model
    try:
        anomaly_detector.load_model("models/anomaly_detector.pkl")
        logger.info("Loaded existing ML model")
    except Exception as e:
        logger.info("No existing ML model found, will use rule-based detection")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
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
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2025-01-18T10:30:00Z"
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
