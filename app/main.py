import logging
import asyncio
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import get_settings
from app.database.connection import connect_to_mongo, close_mongo_connection
from app.api import auth, users, farms, ponds, sensor_readings, alerts, ml, dashboard, mvp_dashboard
from app.mqtt.simple_client import simple_mqtt_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Background task for MQTT
def start_mqtt_background():
    """Start MQTT client in background thread"""
    try:
        logger.info("🚀 Starting MQTT client in background...")
        simple_mqtt_handler.initialize()
        simple_mqtt_handler.setup_client()
        simple_mqtt_handler.connect()
        simple_mqtt_handler.start_loop()  # This blocks
    except Exception as e:
        logger.error(f"❌ Error starting MQTT client: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    # Startup
    logger.info("🌊 Starting Pond Monitoring System MVP...")
    await connect_to_mongo()
    logger.info("✅ Database connected")
    
    # Start MQTT client in background thread
    mqtt_thread = threading.Thread(target=start_mqtt_background, daemon=True)
    mqtt_thread.start()
    logger.info("✅ MQTT client started in background")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Pond Monitoring System...")
    simple_mqtt_handler.stop()
    await close_mongo_connection()
    logger.info("✅ Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Pond Monitoring System MVP",
    description="Real-time pond monitoring with WebSocket, alerts, and SMS notifications",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware - Explicit configuration for better browser compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:3001",  # Alternative React port
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8080",  # Vue dev server
        "http://127.0.0.1:3000",  # Alternative localhost
        "http://127.0.0.1:5173",  # Alternative Vite
        "*"  # Allow all for development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Authorization",
        "Content-Type", 
        "Accept",
        "Origin",
        "X-Requested-With",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ],
    expose_headers=["*"]
)

# Debug middleware to log CORS requests
@app.middleware("http")
async def cors_debug_middleware(request: Request, call_next):
    """Debug middleware to log CORS-related headers"""
    origin = request.headers.get("origin")
    method = request.method
    
    if origin or method == "OPTIONS":
        logger.info(f"CORS Request: {method} {request.url} from Origin: {origin}")
        
    response = await call_next(request)
    
    # Log response CORS headers for debugging
    if origin or method == "OPTIONS":
        cors_headers = {
            k: v for k, v in response.headers.items() 
            if k.lower().startswith('access-control-')
        }
        logger.info(f"CORS Response headers: {cors_headers}")
    
    return response


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
app.include_router(dashboard.router)
app.include_router(mvp_dashboard.router)  # MVP Dashboard with WebSocket


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
            "mvp_dashboard": "/mvp",
            "websocket": "/mvp/ws",
            "documentation": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from app.websocket.manager import websocket_manager
    
    mqtt_status = "connected" if simple_mqtt_handler.is_connected else "disconnected"
    
    return {
        "status": "healthy",
        "timestamp": "2025-01-18T10:30:00Z",
        "services": {
            "api": "running",
            "database": "connected",
            "mqtt_client": mqtt_status,
            "websocket_connections": websocket_manager.get_connection_count()
        }
    }


@app.get("/services/status")
async def services_status():
    """Get detailed status of all services"""
    from app.websocket.manager import websocket_manager
    from app.services.sms_service import sms_service
    
    return {
        "api": {
            "status": "running",
            "version": "1.0.0"
        },
        "database": {
            "status": "connected"
        },
        "mqtt_client": {
            "status": "connected" if simple_mqtt_handler.is_connected else "disconnected",
            "broker": f"{settings.mqtt_broker_host}:{settings.mqtt_broker_port}"
        },
        "websocket": {
            "active_connections": websocket_manager.get_connection_count()
        },
        "sms_service": {
            "status": "enabled" if sms_service.is_enabled() else "disabled"
        }
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
