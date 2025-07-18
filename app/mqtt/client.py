import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any
import paho.mqtt.client as mqtt
from app.config import get_settings
from app.database.connection import get_database
from app.services.database_service import SensorReadingService, AlertService
from app.schemas.schemas import SensorReadingCreate, AlertCreate
from app.ml.anomaly_detection import anomaly_detector

logger = logging.getLogger(__name__)
settings = get_settings()


class MQTTHandler:
    def __init__(self):
        self.client = None
        self.db = None
        self.sensor_service = None
        self.alert_service = None
        self.is_connected = False

    async def initialize(self):
        """Initialize database services"""
        self.db = get_database()
        self.sensor_service = SensorReadingService(self.db)
        self.alert_service = AlertService(self.db)
        logger.info("MQTT Handler initialized")

    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client receives a CONNACK response from the server"""
        if rc == 0:
            self.is_connected = True
            logger.info("Connected to MQTT broker")
            # Subscribe to multiple topic patterns
            topics = [
                ("sensors/+", 0),
                ("status/+", 0),
                ("commands/+", 0),
                (settings.mqtt_topic_pattern, 0)  # Legacy pond data format
            ]
            
            for topic, qos in topics:
                client.subscribe(topic, qos)
                logger.info(f"Subscribed to topic: {topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker. Code: {rc}")

    def on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the server"""
        self.is_connected = False
        logger.info("Disconnected from MQTT broker")

    def on_message(self, client, userdata, msg):
        """Callback for when a PUBLISH message is received from the server"""
        try:
            # Parse the JSON payload
            payload_str = msg.payload.decode('utf-8')
            payload = json.loads(payload_str)
            
            logger.info(f"Received message from {msg.topic}: {payload}")
            
            # Handle different topic types - use thread-safe approach
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # No event loop in current thread, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            if msg.topic.startswith("sensors/temperature"):
                # Handle temperature sensor data
                if loop.is_running():
                    asyncio.ensure_future(self.process_temperature_data(payload))
                else:
                    loop.run_until_complete(self.process_temperature_data(payload))
            elif msg.topic.startswith("status/heartbeat"):
                # Handle heartbeat messages
                if loop.is_running():
                    asyncio.ensure_future(self.process_heartbeat_data(payload))
                else:
                    loop.run_until_complete(self.process_heartbeat_data(payload))
            elif msg.topic.startswith("status/device"):
                # Handle device status
                if loop.is_running():
                    asyncio.ensure_future(self.process_device_status(payload))
                else:
                    loop.run_until_complete(self.process_device_status(payload))
            else:
                # Handle legacy pond sensor data format
                topic_parts = msg.topic.split('/')
                if len(topic_parts) >= 2:
                    pond_id = topic_parts[1]  # farm1/pond_001/data -> pond_001
                    if loop.is_running():
                        asyncio.ensure_future(self.process_sensor_data(pond_id, payload))
                    else:
                        loop.run_until_complete(self.process_sensor_data(pond_id, payload))
                else:
                    logger.warning(f"Unknown topic format: {msg.topic}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON payload: {e}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    async def process_temperature_data(self, data: Dict[str, Any]):
        """Process temperature sensor data from publisher"""
        try:
            device_id = data.get('device_id', 'unknown')
            temperature = data.get('temperature')
            humidity = data.get('humidity')
            timestamp = data.get('timestamp')
            
            logger.info(f"🌡️ Temperature: {temperature}°C, Humidity: {humidity}% from {device_id}")
            
            # You can store this data or process it further
            # For now, just log it
            
        except Exception as e:
            logger.error(f"Error processing temperature data: {e}")

    async def process_heartbeat_data(self, data: Dict[str, Any]):
        """Process heartbeat data from devices"""
        try:
            device_id = data.get('device_id', 'unknown')
            status = data.get('status', 'unknown')
            timestamp = data.get('timestamp')
            
            logger.info(f"💓 Heartbeat from {device_id}: {status}")
            
            # You can track device health here
            
        except Exception as e:
            logger.error(f"Error processing heartbeat data: {e}")

    async def process_device_status(self, data: Dict[str, Any]):
        """Process device status updates"""
        try:
            device_id = data.get('device_id', 'unknown')
            status = data.get('status', 'unknown')
            uptime = data.get('uptime')
            
            logger.info(f"📊 Device {device_id} status: {status}")
            
        except Exception as e:
            logger.error(f"Error processing device status: {e}")

    async def process_sensor_data(self, pond_id: str, data: Dict[str, Any]):
        """Process incoming sensor data"""
        try:
            # Extract timestamp from data or use current time
            timestamp_str = data.get('timestamp')
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except ValueError:
                    timestamp = datetime.utcnow()
            else:
                timestamp = datetime.utcnow()

            # Create sensor reading
            reading_data = SensorReadingCreate(
                pond_id=pond_id,
                timestamp=timestamp,
                temperature=data.get('temperature'),
                ph=data.get('ph'),
                dissolved_oxygen=data.get('dissolved_oxygen'),
                turbidity=data.get('turbidity'),
                ammonia=data.get('ammonia'),
                nitrite=data.get('nitrite'),
                nitrate=data.get('nitrate'),
                salinity=data.get('salinity'),
                water_level=data.get('water_level')
            )

            # Store the reading
            reading = await self.sensor_service.create_reading(reading_data)
            logger.info(f"Stored sensor reading for pond {pond_id}")

            # Perform anomaly detection
            await self.perform_anomaly_detection(reading)

        except Exception as e:
            logger.error(f"Error processing sensor data: {e}")

    async def perform_anomaly_detection(self, reading):
        """Perform anomaly detection on the sensor reading"""
        try:
            # Detect anomaly using ML model
            is_anomaly, anomaly_score, reasons = anomaly_detector.detect_anomaly(reading)

            # Update the reading with anomaly information
            if is_anomaly or anomaly_score > 0:
                await self.sensor_service.update_reading_anomaly(
                    str(reading.id),
                    is_anomaly,
                    anomaly_score,
                    reasons
                )
                logger.info(f"Anomaly detected for pond {reading.pond_id}: {reasons}")

                # Create alert if anomaly is detected
                if is_anomaly:
                    await self.create_anomaly_alert(reading, anomaly_score, reasons)

        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")

    async def create_anomaly_alert(self, reading, anomaly_score: float, reasons: list):
        """Create an alert for detected anomaly"""
        try:
            # Determine severity based on anomaly score
            if anomaly_score >= 0.8:
                severity = "critical"
            elif anomaly_score >= 0.6:
                severity = "high"
            elif anomaly_score >= 0.4:
                severity = "medium"
            else:
                severity = "low"

            # Create alert
            alert_data = AlertCreate(
                pond_id=reading.pond_id,
                alert_type="anomaly",
                severity=severity,
                title=f"Water Quality Anomaly Detected - Pond {reading.pond_id}",
                message=f"Anomaly detected with score {anomaly_score:.2f}. Reasons: {', '.join(reasons)}",
                sensor_reading_id=str(reading.id)
            )

            alert = await self.alert_service.create_alert(alert_data)
            logger.info(f"Created {severity} alert for pond {reading.pond_id}")

        except Exception as e:
            logger.error(f"Error creating anomaly alert: {e}")

    def setup_client(self):
        """Setup MQTT client"""
        # Fix for paho-mqtt 2.0+ compatibility
        try:
            # For paho-mqtt 2.0+
            self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
        except (TypeError, AttributeError):
            # For older versions of paho-mqtt
            self.client = mqtt.Client()
        
        # Set callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

        # Set credentials if provided
        if settings.mqtt_username and settings.mqtt_password:
            self.client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

        logger.info("MQTT client configured")

    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(settings.mqtt_broker_host, settings.mqtt_broker_port, 60)
            logger.info(f"Connecting to MQTT broker at {settings.mqtt_broker_host}:{settings.mqtt_broker_port}")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")

    def start_loop(self):
        """Start the MQTT client loop"""
        if self.client:
            self.client.loop_forever()

    def stop(self):
        """Stop the MQTT client"""
        if self.client:
            self.client.disconnect()
            self.client.loop_stop()
            logger.info("MQTT client stopped")


# Global MQTT handler instance
mqtt_handler = MQTTHandler()
