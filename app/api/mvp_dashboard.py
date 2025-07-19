"""
MVP Dashboard API - Focused on Single Farm Pond Monitoring
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database.connection import get_database
from app.utils.mongo_serializer import serialize_mongo_documents
from app.websocket.manager import websocket_manager

# Helper functions for chart data formatting
def get_parameter_unit(parameter: str) -> str:
    """Get the unit for a sensor parameter"""
    units = {
        "ph": "pH",
        "temperature": "°C",
        "dissolved_oxygen": "mg/L",
        "turbidity": "NTU",
        "nitrate": "mg/L",
        "nitrite": "mg/L", 
        "ammonia": "mg/L",
        "water_level": "m"
    }
    return units.get(parameter, "")

def format_parameter_name(parameter: str) -> str:
    """Format parameter name for display"""
    names = {
        "ph": "pH Level",
        "temperature": "Temperature",
        "dissolved_oxygen": "Dissolved Oxygen",
        "turbidity": "Turbidity",
        "nitrate": "Nitrate",
        "nitrite": "Nitrite",
        "ammonia": "Ammonia",
        "water_level": "Water Level"
    }
    return names.get(parameter, parameter.replace("_", " ").title())

def get_parameter_thresholds(parameter: str) -> dict:
    """Get threshold values for a parameter"""
    from app.config import get_settings
    settings = get_settings()
    
    thresholds = {
        "ph": {
            "min": settings.ph_min,
            "max": settings.ph_max,
            "critical_min": 6.0,
            "critical_max": 9.0,
            "optimal_min": 7.0,
            "optimal_max": 8.5
        },
        "temperature": {
            "min": settings.temperature_min,
            "max": settings.temperature_max,
            "critical_min": 15.0,
            "critical_max": 35.0,
            "optimal_min": 20.0,
            "optimal_max": 30.0
        },
        "dissolved_oxygen": {
            "min": settings.dissolved_oxygen_min,
            "max": settings.dissolved_oxygen_max,
            "critical_min": 3.0,
            "critical_max": 20.0,
            "optimal_min": 5.0,
            "optimal_max": 12.0
        },
        "turbidity": {
            "max": settings.turbidity_max,
            "critical_max": 20.0,
            "optimal_max": 5.0
        },
        "nitrate": {
            "max": settings.nitrate_max,
            "critical_max": 80.0,
            "optimal_max": 20.0
        },
        "nitrite": {
            "max": settings.nitrite_max,
            "critical_max": 1.0,
            "optimal_max": 0.3
        },
        "ammonia": {
            "max": settings.ammonia_max,
            "critical_max": 1.0,
            "optimal_max": 0.2
        },
        "water_level": {
            "min": settings.water_level_min,
            "max": settings.water_level_max,
            "critical_min": 0.2,
            "critical_max": 4.0,
            "optimal_min": 1.0,
            "optimal_max": 3.0
        }
    }
    
    return thresholds.get(parameter, {})
from app.services.alert_service import AlertService
from app.auth.auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mvp", tags=["MVP Dashboard"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time pond monitoring"""
    await websocket_manager.connect(websocket, {"connected_at": datetime.utcnow()})
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            logger.info(f"Received WebSocket message: {data}")
            
            # Echo back or handle specific commands
            await websocket_manager.send_personal_message(
                {"type": "pong", "message": "Connection active"}, 
                websocket
            )
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)


@router.get("/pond/{pond_id}/latest")
async def get_latest_pond_data(
    pond_id: str = "pond_001",
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Get the latest sensor reading for a pond"""
    try:
        # Get latest sensor reading
        latest_reading = await db.sensor_readings.find_one(
            {"pond_id": pond_id},
            sort=[("timestamp", -1)]
        )
        
        if not latest_reading:
            raise HTTPException(status_code=404, detail=f"No data found for pond {pond_id}")

        # Convert ObjectId to string and format response
        latest_reading["id"] = str(latest_reading["_id"])
        del latest_reading["_id"]
        
        # Convert datetime to ISO string
        if "timestamp" in latest_reading and latest_reading["timestamp"]:
            latest_reading["timestamp"] = latest_reading["timestamp"].isoformat()
        if "created_at" in latest_reading and latest_reading["created_at"]:
            latest_reading["created_at"] = latest_reading["created_at"].isoformat()

        # Get active alerts count
        active_alerts_count = await db.alerts.count_documents({
            "pond_id": pond_id,
            "is_resolved": False
        })

        return {
            "pond_id": pond_id,
            "latest_reading": latest_reading,
            "active_alerts": active_alerts_count,
            "status": "active" if latest_reading else "inactive",
            "last_updated": latest_reading.get("timestamp", "").isoformat() if latest_reading.get("timestamp") else None
        }

    except Exception as e:
        logger.error(f"Error getting latest pond data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/pond/{pond_id}/history")
async def get_pond_history(
    pond_id: str = "pond_001",
    hours: int = Query(24, description="Hours of history to fetch"),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Get historical sensor data for a pond"""
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        cursor = db.sensor_readings.find({
            "pond_id": pond_id,
            "timestamp": {"$gte": start_time}
        }).sort("timestamp", 1)  # Ascending order for time series
        
        readings = await cursor.to_list(length=1000)  # Limit to 1000 readings
        
        # Format readings
        formatted_readings = []
        for reading in readings:
            reading["id"] = str(reading["_id"])
            del reading["_id"]
            
            # Convert datetime to ISO string
            if "timestamp" in reading and reading["timestamp"]:
                reading["timestamp"] = reading["timestamp"].isoformat()
            if "created_at" in reading and reading["created_at"]:
                reading["created_at"] = reading["created_at"].isoformat()
                
            formatted_readings.append(reading)

        return {
            "pond_id": pond_id,
            "period_hours": hours,
            "total_readings": len(formatted_readings),
            "readings": formatted_readings
        }

    except Exception as e:
        logger.error(f"Error getting pond history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/pond/{pond_id}/alerts")
async def get_pond_alerts(
    pond_id: str = "pond_001",
    active_only: bool = Query(True, description="Show only active alerts"),
    limit: int = Query(50, description="Maximum number of alerts to return"),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Get alerts for a pond"""
    try:
        alert_service = AlertService(db)
        
        # Build query
        query = {"pond_id": pond_id}
        if active_only:
            query["is_resolved"] = False

        # Get alerts
        cursor = db.alerts.find(query).sort("created_at", -1).limit(limit)
        alerts = await cursor.to_list(length=limit)

        # Format alerts
        formatted_alerts = []
        for alert in alerts:
            alert["id"] = str(alert["_id"])
            del alert["_id"]
            
            # Convert datetime to ISO string
            if "created_at" in alert and alert["created_at"]:
                alert["created_at"] = alert["created_at"].isoformat()
            if "resolved_at" in alert and alert["resolved_at"]:
                alert["resolved_at"] = alert["resolved_at"].isoformat()
                
            formatted_alerts.append(alert)

        # Get alert statistics
        stats = await alert_service.get_alert_statistics(pond_id, days=7)

        return {
            "pond_id": pond_id,
            "alerts": formatted_alerts,
            "statistics": stats,
            "total_returned": len(formatted_alerts)
        }

    except Exception as e:
        logger.error(f"Error getting pond alerts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/alerts/active")
async def get_active_alerts(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Get all active alerts across all ponds"""
    try:
        cursor = db.alerts.find({
            "is_resolved": False
        }).sort("created_at", -1)
        
        alerts = await cursor.to_list(length=100)

        # Use the serializer to properly handle ObjectIds and datetimes
        formatted_alerts = serialize_mongo_documents(alerts)

        # Group by severity
        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for alert in formatted_alerts:
            severity = alert.get("severity", "low")
            by_severity[severity] = by_severity.get(severity, 0) + 1

        return {
            "total_active_alerts": len(formatted_alerts),
            "alerts": formatted_alerts,
            "by_severity": by_severity
        }

    except Exception as e:
        logger.error(f"Error getting active alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/alert/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Resolve an alert"""
    try:
        alert_service = AlertService(db)
        success = await alert_service.resolve_alert(alert_id, current_user.get("id"))
        
        if success:
            return {"message": "Alert resolved successfully", "alert_id": alert_id}
        else:
            raise HTTPException(status_code=404, detail="Alert not found")

    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/dashboard/overview")
async def get_dashboard_overview(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive dashboard overview for MVP"""
    try:
        # Get total readings count
        total_readings = await db.sensor_readings.count_documents({})
        
        # Get latest readings for each pond
        latest_readings_pipeline = [
            {"$sort": {"timestamp": -1}},
            {"$group": {
                "_id": "$pond_id",
                "latest_reading": {"$first": "$$ROOT"}
            }}
        ]
        
        cursor = db.sensor_readings.aggregate(latest_readings_pipeline)
        pond_data = await cursor.to_list(length=None)

        # Get active alerts
        active_alerts = await db.alerts.count_documents({"is_resolved": False})
        
        # Get critical alerts
        critical_alerts = await db.alerts.count_documents({
            "is_resolved": False,
            "severity": "critical"
        })

        # Get alert statistics
        alert_service = AlertService(db)
        alert_stats = await alert_service.get_alert_statistics(days=7)

        # Format pond data
        ponds = []
        for pond in pond_data:
            pond_id = pond["_id"]
            latest = pond["latest_reading"]
            
            # Calculate pond status
            status = "active"
            if latest.get("timestamp"):
                time_diff = datetime.utcnow() - latest["timestamp"]
                if time_diff > timedelta(minutes=30):
                    status = "inactive"

            ponds.append({
                "pond_id": pond_id,
                "status": status,
                "latest_reading": {
                    "timestamp": latest.get("timestamp", "").isoformat() if latest.get("timestamp") else None,
                    "ph": latest.get("ph"),
                    "temperature": latest.get("temperature"),
                    "dissolved_oxygen": latest.get("dissolved_oxygen"),
                    "water_level": latest.get("water_level")
                }
            })

        return {
            "summary": {
                "total_ponds": len(ponds),
                "active_ponds": len([p for p in ponds if p["status"] == "active"]),
                "total_readings": total_readings,
                "active_alerts": active_alerts,
                "critical_alerts": critical_alerts
            },
            "ponds": ponds,
            "alert_statistics": alert_stats,
            "websocket_connections": websocket_manager.get_connection_count()
        }

    except Exception as e:
        logger.error(f"Error getting dashboard overview: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/pond/{pond_id}/chart-data")
async def get_pond_chart_data(
    pond_id: str = "pond_001",
    hours: int = Query(24, description="Hours of data to fetch for charts"),
    parameters: str = Query("ph,temperature,dissolved_oxygen,water_level", description="Comma-separated list of parameters"),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Get sensor data formatted for charts by pond ID"""
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Parse requested parameters
        requested_params = [param.strip() for param in parameters.split(',')]
        
        # Get sensor readings for the specified time period
        cursor = db.sensor_readings.find({
            "pond_id": pond_id,
            "timestamp": {"$gte": start_time}
        }).sort("timestamp", 1)  # Ascending for time series
        
        readings = await cursor.to_list(length=2000)  # Limit for performance
        
        if not readings:
            return {
                "pond_id": pond_id,
                "period_hours": hours,
                "parameters": requested_params,
                "chart_data": {},
                "metadata": {
                    "total_points": 0,
                    "start_time": start_time.isoformat(),
                    "end_time": datetime.utcnow().isoformat()
                }
            }

        # Prepare chart data structure
        chart_data = {}
        
        # Initialize data arrays for each parameter
        for param in requested_params:
            chart_data[param] = {
                "labels": [],  # Timestamps
                "values": [],  # Parameter values
                "unit": get_parameter_unit(param),
                "name": format_parameter_name(param)
            }
        
        # Process readings and organize data for charts
        for reading in readings:
            timestamp = reading.get("timestamp")
            if timestamp:
                # Format timestamp for chart labels
                formatted_time = timestamp.strftime("%H:%M") if isinstance(timestamp, datetime) else timestamp
                
                for param in requested_params:
                    value = reading.get(param)
                    if value is not None:
                        chart_data[param]["labels"].append(formatted_time)
                        chart_data[param]["values"].append(round(float(value), 2))

        # Calculate statistics for each parameter
        for param in requested_params:
            values = chart_data[param]["values"]
            if values:
                chart_data[param]["stats"] = {
                    "min": min(values),
                    "max": max(values),
                    "avg": round(sum(values) / len(values), 2),
                    "latest": values[-1] if values else None,
                    "count": len(values)
                }
            else:
                chart_data[param]["stats"] = {
                    "min": None, "max": None, "avg": None, "latest": None, "count": 0
                }

        return {
            "pond_id": pond_id,
            "period_hours": hours,
            "parameters": requested_params,
            "chart_data": chart_data,
            "metadata": {
                "total_points": len(readings),
                "start_time": start_time.isoformat(),
                "end_time": datetime.utcnow().isoformat(),
                "available_parameters": ["ph", "temperature", "dissolved_oxygen", "turbidity", 
                                       "nitrate", "nitrite", "ammonia", "water_level"]
            }
        }

    except Exception as e:
        logger.error(f"Error getting chart data for pond {pond_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/pond/{pond_id}/realtime-chart")
async def get_realtime_chart_data(
    pond_id: str = "pond_001",
    parameter: str = Query("temperature", description="Single parameter for real-time chart"),
    minutes: int = Query(60, description="Minutes of recent data"),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Get real-time data for live charts (single parameter)"""
    try:
        start_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        cursor = db.sensor_readings.find({
            "pond_id": pond_id,
            "timestamp": {"$gte": start_time}
        }).sort("timestamp", 1)
        
        readings = await cursor.to_list(length=500)  # Limit for real-time performance
        
        # Format for real-time charts
        timestamps = []
        values = []
        
        for reading in readings:
            timestamp = reading.get("timestamp")
            value = reading.get(parameter)
            
            if timestamp and value is not None:
                timestamps.append(timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp)
                values.append(round(float(value), 2))

        # Get threshold information for the parameter
        thresholds = get_parameter_thresholds(parameter)
        
        return {
            "pond_id": pond_id,
            "parameter": parameter,
            "period_minutes": minutes,
            "data": {
                "timestamps": timestamps,
                "values": values,
                "unit": get_parameter_unit(parameter),
                "name": format_parameter_name(parameter)
            },
            "thresholds": thresholds,
            "latest_value": values[-1] if values else None,
            "data_points": len(values),
            "last_updated": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting real-time chart data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/system/status")
async def get_system_status(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Get system status for monitoring"""
    try:
        # Check database connectivity
        db_status = "connected"
        try:
            await db.sensor_readings.find_one()
        except Exception:
            db_status = "disconnected"

        # Get SMS service status
        from app.services.sms_service import sms_service
        sms_status = "enabled" if sms_service.is_enabled() else "disabled"

        # Get latest reading timestamp
        latest_reading = await db.sensor_readings.find_one({}, sort=[("timestamp", -1)])
        last_data_time = latest_reading.get("timestamp").isoformat() if latest_reading and latest_reading.get("timestamp") else None

        return {
            "system_status": "operational",
            "database": db_status,
            "sms_service": sms_status,
            "websocket_connections": websocket_manager.get_connection_count(),
            "last_data_received": last_data_time,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/test/sms")
async def test_sms_service(
    current_user: dict = Depends(get_current_user)
):
    """Test SMS service configuration"""
    try:
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Admin access required")

        from app.services.sms_service import sms_service
        
        if not sms_service.is_enabled():
            return {"status": "disabled", "message": "SMS service is not configured"}

        success = await sms_service.test_sms()
        
        return {
            "status": "success" if success else "failed",
            "message": "Test SMS sent successfully" if success else "Failed to send test SMS"
        }

    except Exception as e:
        logger.error(f"Error testing SMS service: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
