"""
Simple MQTT Client for MVP - Real-time Pond Monitoring
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import paho.mqtt.client as mqtt
import pymongo
from app.config import get_settings
from app.websocket.manager import websocket_manager

logger = logging.getLogger(__name__)
settings = get_settings()


class SimpleMQTTHandler:
    def __init__(self):
        self.client = None
        self.is_connected = False
        # Synchronous MongoDB connection for MQTT processing
        self.sync_mongo_client = None
        self.sync_db = None

    def initialize(self):
        """Initialize database connection"""
        try:
            self.sync_mongo_client = pymongo.MongoClient(settings.mongodb_url)
            self.sync_db = self.sync_mongo_client[settings.database_name]
            logger.info("Simple MQTT Handler initialized")
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB connection: {e}")

    def setup_client(self):
        """Set up MQTT client with callbacks"""
        self.client = mqtt.Client(client_id="pond_monitoring_mvp")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        # Set credentials if provided
        if settings.mqtt_username and settings.mqtt_password:
            self.client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

    def on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            self.is_connected = True
            logger.info("🟢 Connected to MQTT broker")
            # Subscribe to pond data topics
            topics = [
                ("sensors/pond_data", 0),
                ("sensors/+", 0),
            ]
            
            for topic, qos in topics:
                client.subscribe(topic, qos)
                logger.info(f"📡 Subscribed to: {topic}")
        else:
            logger.error(f"🔴 Failed to connect to MQTT broker. Code: {rc}")

    def on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        self.is_connected = False
        logger.info("📴 Disconnected from MQTT broker")

    def on_message(self, client, userdata, msg):
        """Process incoming MQTT messages"""
        try:
            # Parse JSON payload
            payload_str = msg.payload.decode('utf-8')
            payload = json.loads(payload_str)
            
            logger.info(f"📩 Received from {msg.topic}: {payload}")
            
            # Process based on topic
            if msg.topic == "sensors/pond_data":
                self._process_pond_data(payload)
            elif msg.topic.startswith("sensors/"):
                self._process_sensor_data(msg.topic, payload)
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {e}")
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")

    def _process_pond_data(self, data: Dict[str, Any]):
        """Process pond sensor data and check for alerts"""
        try:
            pond_id = data.get('pond_id', 'pond_001')  # Default to pond_001 for MVP
            
            # Store sensor reading
            reading_doc = {
                'pond_id': pond_id,
                'device_id': data.get('device_id', 'unknown'),
                'timestamp': datetime.utcnow(),
                'ph': data.get('ph'),
                'temperature': data.get('temperature'),
                'dissolved_oxygen': data.get('dissolved_oxygen'),
                'turbidity': data.get('turbidity'),
                'nitrate': data.get('nitrate'),
                'nitrite': data.get('nitrite'),
                'ammonia': data.get('ammonia'),
                'water_level': data.get('water_level'),
                'created_at': datetime.utcnow()
            }

            # Insert into database
            result = self.sync_db.sensor_readings.insert_one(reading_doc)
            logger.info(f"💾 Stored reading for {pond_id}: {result.inserted_id}")

            # Broadcast to WebSocket clients (schedule if no event loop)
            websocket_data = {
                "pond_id": pond_id,
                "timestamp": reading_doc['timestamp'].isoformat(),
                **{k: v for k, v in reading_doc.items() if k not in ['_id', 'created_at']}
            }
            
            # Schedule WebSocket broadcast safely
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(websocket_manager.broadcast_sensor_data(websocket_data))
                else:
                    asyncio.run(websocket_manager.broadcast_sensor_data(websocket_data))
            except RuntimeError:
                # No event loop running, skip WebSocket broadcast
                logger.debug("No event loop available for WebSocket broadcast")
            except Exception as e:
                logger.error(f"WebSocket broadcast error: {e}")

            # Check for threshold violations
            self._check_thresholds(pond_id, data, result.inserted_id)

        except Exception as e:
            logger.error(f"❌ Error processing pond data: {e}")

    def _process_sensor_data(self, topic: str, data: Dict[str, Any]):
        """Process generic sensor data"""
        try:
            # Extract pond_id from topic or data
            pond_id = data.get('pond_id', 'pond_001')
            logger.info(f"🌊 Processing sensor data for {pond_id}")
            
            # Forward to pond data processor
            self._process_pond_data(data)
            
        except Exception as e:
            logger.error(f"❌ Error processing sensor data: {e}")

    def _check_thresholds(self, pond_id: str, sensor_data: Dict[str, Any], reading_id):
        """Check sensor values against thresholds and create alerts"""
        try:
            alerts_created = []
            
            # Define thresholds for MVP
            thresholds = {
                'ph': {'min': settings.ph_min, 'max': settings.ph_max, 'critical_min': 6.0, 'critical_max': 9.0},
                'temperature': {'min': settings.temperature_min, 'max': settings.temperature_max, 'critical_min': 15.0, 'critical_max': 35.0},
                'dissolved_oxygen': {'min': settings.dissolved_oxygen_min, 'max': settings.dissolved_oxygen_max, 'critical_min': 3.0},
                'turbidity': {'max': settings.turbidity_max, 'critical_max': 20.0},
                'nitrate': {'max': settings.nitrate_max, 'critical_max': 80.0},
                'ammonia': {'max': settings.ammonia_max, 'critical_max': 1.0},
                'water_level': {'min': settings.water_level_min, 'max': settings.water_level_max}
            }

            for parameter, limits in thresholds.items():
                value = sensor_data.get(parameter)
                if value is None:
                    continue

                alert_data = None
                severity = None
                message = ""

                # Check critical limits
                if 'critical_min' in limits and value < limits['critical_min']:
                    severity = "critical"
                    message = f"CRITICAL: {parameter.upper()} dangerously low: {value} (limit: {limits['critical_min']})"
                elif 'critical_max' in limits and value > limits['critical_max']:
                    severity = "critical"
                    message = f"CRITICAL: {parameter.upper()} dangerously high: {value} (limit: {limits['critical_max']})"
                # Check normal limits
                elif 'min' in limits and value < limits['min']:
                    severity = "high"
                    message = f"HIGH: {parameter.upper()} below threshold: {value} (limit: {limits['min']})"
                elif 'max' in limits and value > limits['max']:
                    severity = "high"
                    message = f"HIGH: {parameter.upper()} above threshold: {value} (limit: {limits['max']})"

                # Create alert if threshold violated
                if severity:
                    # Check if similar alert exists recently (avoid spam)
                    recent_alert = self.sync_db.alerts.find_one({
                        "pond_id": pond_id,
                        "parameter": parameter,
                        "is_resolved": False,
                        "created_at": {"$gte": datetime.utcnow().replace(microsecond=0).replace(second=0) - timedelta(minutes=15)}
                    })

                    if not recent_alert:
                        alert_doc = {
                            "pond_id": pond_id,
                            "sensor_reading_id": reading_id,
                            "alert_type": f"{parameter}_{severity}",
                            "parameter": parameter,
                            "current_value": value,
                            "threshold_value": limits.get('min', limits.get('max')),
                            "severity": severity,
                            "message": message,
                            "is_resolved": False,
                            "sms_sent": False,
                            "created_at": datetime.utcnow()
                        }

                        alert_result = self.sync_db.alerts.insert_one(alert_doc)
                        alert_doc["_id"] = alert_result.inserted_id
                        alerts_created.append(alert_doc)

                        logger.warning(f"🚨 {severity.upper()} ALERT for {pond_id}: {message}")

                        # Schedule SMS and WebSocket notifications
                        self._schedule_notifications(alert_doc)

            if alerts_created:
                logger.info(f"📢 Created {len(alerts_created)} alerts for {pond_id}")

        except Exception as e:
            logger.error(f"❌ Error checking thresholds: {e}")

    def _schedule_notifications(self, alert_doc: Dict[str, Any]):
        """Schedule SMS and WebSocket notifications for alerts"""
        try:
            # Schedule WebSocket broadcast
            websocket_alert = {
                "id": str(alert_doc["_id"]),
                "pond_id": alert_doc["pond_id"],
                "parameter": alert_doc["parameter"],
                "current_value": alert_doc["current_value"],
                "threshold_value": alert_doc["threshold_value"],
                "severity": alert_doc["severity"],
                "message": alert_doc["message"],
                "created_at": alert_doc["created_at"].isoformat()
            }
            
            # Schedule WebSocket broadcast safely
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(websocket_manager.broadcast_alert(websocket_alert))
                else:
                    asyncio.run(websocket_manager.broadcast_alert(websocket_alert))
            except RuntimeError:
                logger.debug("No event loop available for WebSocket alert broadcast")
            except Exception as e:
                logger.error(f"WebSocket alert broadcast error: {e}")

            # Schedule SMS for high/critical alerts safely
            if alert_doc["severity"] in ["high", "critical"]:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self._send_sms_alert(alert_doc))
                    else:
                        asyncio.run(self._send_sms_alert(alert_doc))
                except RuntimeError:
                    logger.debug("No event loop available for SMS alert")
                except Exception as e:
                    logger.error(f"SMS alert scheduling error: {e}")

        except Exception as e:
            logger.error(f"❌ Error scheduling notifications: {e}")

    async def _send_sms_alert(self, alert_doc: Dict[str, Any]):
        """Send SMS alert using Twilio"""
        try:
            from app.services.sms_service import sms_service
            
            pond_id = alert_doc["pond_id"]
            parameter = alert_doc["parameter"]
            value = alert_doc["current_value"]
            threshold = alert_doc["threshold_value"]
            severity = alert_doc["severity"]

            if severity == "critical":
                sms_sent = await sms_service.send_critical_alert(pond_id, parameter, value, threshold)
            else:
                sms_sent = await sms_service.send_high_alert(pond_id, parameter, value, threshold)

            # Update SMS status in database
            if sms_sent:
                self.sync_db.alerts.update_one(
                    {"_id": alert_doc["_id"]},
                    {"$set": {"sms_sent": True}}
                )
                logger.info(f"📱 SMS sent for alert: {alert_doc['_id']}")

        except Exception as e:
            logger.error(f"❌ Error sending SMS alert: {e}")

    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(settings.mqtt_broker_host, settings.mqtt_broker_port, 60)
            logger.info(f"🔄 Connecting to MQTT broker: {settings.mqtt_broker_host}:{settings.mqtt_broker_port}")
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")

    def start_loop(self):
        """Start MQTT loop"""
        self.client.loop_forever()

    def stop(self):
        """Stop MQTT client"""
        if self.client:
            self.client.disconnect()
            self.client.loop_stop()
        if self.sync_mongo_client:
            self.sync_mongo_client.close()
        logger.info("🛑 MQTT Handler stopped")


# Global instance
simple_mqtt_handler = SimpleMQTTHandler()
