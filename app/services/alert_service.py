"""
Alert Service for Monitoring Sensor Thresholds and Managing Alerts
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.config import get_settings
from app.models.models import Alert, AlertSeverity, SensorReading
from app.services.sms_service import sms_service
from app.websocket.manager import websocket_manager

logger = logging.getLogger(__name__)
settings = get_settings()


class AlertService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.alerts_collection = db.alerts

    async def check_sensor_thresholds(self, sensor_reading: Dict[str, Any]) -> List[Alert]:
        """Check sensor reading against thresholds and create alerts"""
        alerts = []
        pond_id = sensor_reading.get("pond_id", "unknown")
        reading_id = sensor_reading.get("_id")

        # Define thresholds with severity levels
        threshold_checks = [
            {
                "parameter": "ph",
                "value": sensor_reading.get("ph"),
                "min_threshold": settings.ph_min,
                "max_threshold": settings.ph_max,
                "critical_min": 6.0,
                "critical_max": 9.0
            },
            {
                "parameter": "temperature",
                "value": sensor_reading.get("temperature"),
                "min_threshold": settings.temperature_min,
                "max_threshold": settings.temperature_max,
                "critical_min": 15.0,
                "critical_max": 35.0
            },
            {
                "parameter": "dissolved_oxygen",
                "value": sensor_reading.get("dissolved_oxygen"),
                "min_threshold": settings.dissolved_oxygen_min,
                "max_threshold": settings.dissolved_oxygen_max,
                "critical_min": 3.0,
                "critical_max": 20.0
            },
            {
                "parameter": "turbidity",
                "value": sensor_reading.get("turbidity"),
                "max_threshold": settings.turbidity_max,
                "critical_max": 20.0
            },
            {
                "parameter": "nitrate",
                "value": sensor_reading.get("nitrate"),
                "max_threshold": settings.nitrate_max,
                "critical_max": 80.0
            },
            {
                "parameter": "nitrite",
                "value": sensor_reading.get("nitrite"),
                "max_threshold": settings.nitrite_max,
                "critical_max": 1.0
            },
            {
                "parameter": "ammonia",
                "value": sensor_reading.get("ammonia"),
                "max_threshold": settings.ammonia_max,
                "critical_max": 1.0
            },
            {
                "parameter": "water_level",
                "value": sensor_reading.get("water_level"),
                "min_threshold": settings.water_level_min,
                "max_threshold": settings.water_level_max,
                "critical_min": 0.2,
                "critical_max": 4.0
            }
        ]

        for check in threshold_checks:
            if check["value"] is None:
                continue

            parameter = check["parameter"]
            value = check["value"]
            alert = None

            # Check critical thresholds
            if ("critical_min" in check and value < check["critical_min"]) or \
               ("critical_max" in check and value > check["critical_max"]):
                threshold = check.get("critical_min", check.get("critical_max"))
                alert = await self._create_alert(
                    pond_id=pond_id,
                    parameter=parameter,
                    current_value=value,
                    threshold_value=threshold,
                    severity=AlertSeverity.CRITICAL,
                    alert_type=f"{parameter}_critical",
                    reading_id=reading_id
                )

            # Check high severity thresholds
            elif ("min_threshold" in check and value < check["min_threshold"]) or \
                 ("max_threshold" in check and value > check["max_threshold"]):
                threshold = check.get("min_threshold", check.get("max_threshold"))
                alert = await self._create_alert(
                    pond_id=pond_id,
                    parameter=parameter,
                    current_value=value,
                    threshold_value=threshold,
                    severity=AlertSeverity.HIGH,
                    alert_type=f"{parameter}_high",
                    reading_id=reading_id
                )

            if alert:
                alerts.append(alert)

        return alerts

    async def _create_alert(self, pond_id: str, parameter: str, current_value: float, 
                          threshold_value: float, severity: AlertSeverity, 
                          alert_type: str, reading_id: Optional[str] = None) -> Alert:
        """Create and store a new alert"""
        
        # Check if similar alert already exists (avoid spam)
        existing_alert = await self.alerts_collection.find_one({
            "pond_id": pond_id,
            "parameter": parameter,
            "alert_type": alert_type,
            "is_resolved": False,
            "created_at": {"$gte": datetime.utcnow() - timedelta(minutes=15)}  # Don't spam within 15 minutes
        })

        if existing_alert:
            logger.debug(f"Similar alert already exists for {pond_id} - {parameter}")
            return None

        # Create alert message
        direction = "below" if current_value < threshold_value else "above"
        message = f"{parameter.replace('_', ' ').title()} is {direction} threshold: {current_value} (limit: {threshold_value})"

        alert_data = {
            "pond_id": pond_id,
            "sensor_reading_id": reading_id,
            "alert_type": alert_type,
            "parameter": parameter,
            "current_value": current_value,
            "threshold_value": threshold_value,
            "severity": severity.value,
            "message": message,
            "is_resolved": False,
            "sms_sent": False,
            "created_at": datetime.utcnow()
        }

        # Insert alert into database
        result = await self.alerts_collection.insert_one(alert_data)
        alert_data["_id"] = result.inserted_id

        logger.info(f"Created {severity.value} alert for {pond_id}: {message}")

        # Send SMS for high and critical alerts
        if severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
            sms_sent = False
            if severity == AlertSeverity.CRITICAL:
                sms_sent = await sms_service.send_critical_alert(pond_id, parameter, current_value, threshold_value)
            elif severity == AlertSeverity.HIGH:
                sms_sent = await sms_service.send_high_alert(pond_id, parameter, current_value, threshold_value)
            
            # Update SMS status
            if sms_sent:
                await self.alerts_collection.update_one(
                    {"_id": result.inserted_id},
                    {"$set": {"sms_sent": True}}
                )
                alert_data["sms_sent"] = True

        # Broadcast alert via WebSocket
        await websocket_manager.broadcast_alert({
            "id": str(result.inserted_id),
            "pond_id": pond_id,
            "parameter": parameter,
            "current_value": current_value,
            "threshold_value": threshold_value,
            "severity": severity.value,
            "message": message,
            "sms_sent": alert_data["sms_sent"],
            "created_at": alert_data["created_at"].isoformat()
        })

        # Convert to Alert model
        alert = Alert(**alert_data)
        return alert

    async def get_active_alerts(self, pond_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all active (unresolved) alerts"""
        query = {"is_resolved": False}
        if pond_id:
            query["pond_id"] = pond_id

        cursor = self.alerts_collection.find(query).sort("created_at", -1)
        alerts = await cursor.to_list(length=100)
        
        # Convert ObjectId to string
        for alert in alerts:
            alert["id"] = str(alert["_id"])
            
        return alerts

    async def get_alert_details(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed alert information"""
        from bson import ObjectId
        
        try:
            alert = await self.alerts_collection.find_one({"_id": ObjectId(alert_id)})
            if alert:
                alert["id"] = str(alert["_id"])
                return alert
            return None
        except Exception as e:
            logger.error(f"Error getting alert details: {e}")
            return None

    async def resolve_alert(self, alert_id: str, user_id: Optional[str] = None) -> bool:
        """Mark alert as resolved"""
        from bson import ObjectId
        
        try:
            result = await self.alerts_collection.update_one(
                {"_id": ObjectId(alert_id)},
                {
                    "$set": {
                        "is_resolved": True,
                        "resolved_at": datetime.utcnow(),
                        "resolved_by": user_id
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Alert {alert_id} resolved by user {user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            return False

    async def get_alert_statistics(self, pond_id: Optional[str] = None, 
                                 days: int = 7) -> Dict[str, Any]:
        """Get alert statistics for dashboard"""
        start_date = datetime.utcnow() - timedelta(days=days)
        match_filter = {"created_at": {"$gte": start_date}}
        
        if pond_id:
            match_filter["pond_id"] = pond_id

        pipeline = [
            {"$match": match_filter},
            {
                "$group": {
                    "_id": {
                        "severity": "$severity",
                        "parameter": "$parameter"
                    },
                    "count": {"$sum": 1},
                    "avg_value": {"$avg": "$current_value"},
                    "latest_alert": {"$max": "$created_at"}
                }
            }
        ]

        cursor = self.alerts_collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)

        # Process results
        stats = {
            "total_alerts": 0,
            "by_severity": {"low": 0, "medium": 0, "high": 0, "critical": 0},
            "by_parameter": {},
            "active_alerts": len(await self.get_active_alerts(pond_id)),
            "period_days": days
        }

        for result in results:
            severity = result["_id"]["severity"]
            parameter = result["_id"]["parameter"]
            count = result["count"]

            stats["total_alerts"] += count
            stats["by_severity"][severity] += count
            
            if parameter not in stats["by_parameter"]:
                stats["by_parameter"][parameter] = 0
            stats["by_parameter"][parameter] += count

        return stats
