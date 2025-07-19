import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any
import paho.mqtt.client as mqtt
import pymongo
from bson import ObjectId
from app.config import get_settings
from app.database.connection import get_database
from app.services.alert_service import AlertService
from app.schemas.schemas import SensorReadingCreate
from app.websocket.manager import websocket_manager

logger = logging.getLogger(__name__)
settings = get_settings()


class MQTTHandler:
    def __init__(self):
        self.client = None
        self.db = None
        self.alert_service = None
        self.is_connected = False
        # Add synchronous MongoDB connection for MQTT processing
        self.sync_mongo_client = None
        self.sync_db = None
        self._message_queue = []

    async def initialize(self):
        """Initialize database services"""
        self.db = get_database()
        self.alert_service = AlertService(self.db)
        
        # Initialize synchronous MongoDB connection for MQTT processing
        self.sync_mongo_client = pymongo.MongoClient(settings.mongodb_url)
        self.sync_db = self.sync_mongo_client[settings.database_name]
        
        logger.info("MQTT Handler initialized with alert service and WebSocket integration")

    async def initialize(self):
        """Initialize database services"""
        self.db = get_database()
        self.sensor_service = SensorReadingService(self.db)
        self.alert_service = AlertService(self.db)
        
        # Initialize synchronous MongoDB connection for MQTT processing
        self.sync_mongo_client = pymongo.MongoClient(settings.mongodb_url)
        self.sync_db = self.sync_mongo_client[settings.database_name]
        
        logger.info("MQTT Handler initialized with both async and sync database connections")

    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client receives a CONNACK response from the server"""
        if rc == 0:
            self.is_connected = True
            logger.info("Connected to MQTT broker")
            # Subscribe to the new pond data topic
            topics = [
                ("sensors/pond_data", 0),  # Main topic for pond sensor data
                ("sensors/+", 0),          # Wildcard for other sensor topics
                ("status/+", 0),           # Status updates
                ("commands/+", 0)          # Commands
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
            logger.info(f"Raw payload from {msg.topic}: '{payload_str}'")
            payload = json.loads(payload_str)

            
            logger.info(f"Received message from {msg.topic}: {payload}")
            
            # Store the message for processing in the main event loop
            if not hasattr(self, '_message_queue'):
                self._message_queue = []
            
            self._message_queue.append((msg.topic, payload))
            
            # Process the message immediately in a new thread if possible
            # This ensures the database operations run properly
            import threading
            thread = threading.Thread(target=self._process_message_sync, args=(msg.topic, payload))
            thread.daemon = True
            thread.start()
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON payload: {e}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def _process_message_sync(self, topic: str, payload: dict):
        """Process message in a synchronous context with direct database operations"""
        try:
            # Process the message based on topic using synchronous database operations
            if topic == "sensors/pond_data":
                # Main pond sensor data
                self._process_pond_sensor_data_sync(payload)
            elif topic.startswith("sensors/water_quality"):
                # Legacy water quality data
                self._process_water_quality_sync(payload)
            elif topic.startswith("status/heartbeat"):
                self._process_heartbeat_sync(payload)
            elif topic.startswith("status/device"):
                self._process_device_status_sync(payload)
            elif topic.startswith("farm1/") and topic.endswith("/data"):
                # Legacy farm data format
                topic_parts = topic.split('/')
                if len(topic_parts) >= 3:  # farm1/pond_001/data
                    pond_id = topic_parts[1]  # Extract pond_001
                    self._process_sensor_data_sync(pond_id, payload)
                else:
                    logger.warning(f"Invalid pond topic format: {topic}")
            elif topic.startswith("sensors/temperature"):
                self._process_temperature_sync(payload)
            else:
                logger.info(f"Skipping unknown topic: {topic}")
            
        except Exception as e:
            logger.error(f"Error processing message in sync context: {e}")

    def _process_pond_sensor_data_sync(self, data: Dict[str, Any]):
        """Process pond sensor data from simulators"""
        try:
            pond_id = data.get('pond_id', 'unknown')
            device_id = data.get('device_id', 'unknown')
            
            logger.info(f"🏊 Pond sensor data from {device_id} for {pond_id}")
            
            # Extract and validate timestamp
            timestamp_str = data.get('timestamp')
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    timestamp = datetime.utcnow()
                    logger.warning(f"Invalid timestamp format for {pond_id}, using current time")
            else:
                timestamp = datetime.utcnow()

            # Create sensor reading document with the 8 core sensor parameters
            reading_doc = {
                'pond_id': pond_id,
                'device_id': device_id,
                'timestamp': timestamp,
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

            # Store the reading using synchronous MongoDB
            result = self.sync_db.sensor_readings.insert_one(reading_doc)
            
            # Log the stored data
            logger.info(f"✅ Stored sensor reading for {pond_id}: pH={data.get('ph')}, Temp={data.get('temperature')}°C, DO={data.get('dissolved_oxygen')}mg/L, ID={result.inserted_id}")
            
            # Check for critical alerts
            self._check_critical_conditions_sync(pond_id, data)

        except Exception as e:
            logger.error(f"❌ Error processing pond sensor data: {e}")
            
    def _process_water_quality_sync(self, data: Dict[str, Any]):
        """Process water quality data synchronously"""
        try:
            pond_id = data.get('pond_id', 'unknown')
            device_id = data.get('device_id', 'unknown')
            
            logger.info(f"💧 Water quality data from {device_id} for pond {pond_id}")
            
            # Process as sensor data
            self._process_sensor_data_sync(pond_id, data)
            
        except Exception as e:
            logger.error(f"Error processing water quality data: {e}")
            
    def _process_heartbeat_sync(self, data: Dict[str, Any]):
        """Process heartbeat data synchronously"""
        try:
            device_id = data.get('device_id', 'unknown')
            status = data.get('status', 'unknown')
            
            logger.info(f"💓 Heartbeat from {device_id}: {status}")
            
        except Exception as e:
            logger.error(f"Error processing heartbeat: {e}")
            
    def _process_device_status_sync(self, data: Dict[str, Any]):
        """Process device status synchronously"""
        try:
            device_id = data.get('device_id', 'unknown')
            status = data.get('status', 'unknown')
            
            logger.info(f"📊 Device {device_id} status: {status}")
            
        except Exception as e:
            logger.error(f"Error processing device status: {e}")
            
    def _process_temperature_sync(self, data: Dict[str, Any]):
        """Process temperature data synchronously"""
        try:
            device_id = data.get('device_id', 'unknown')
            temperature = data.get('temperature')
            humidity = data.get('humidity')
            
            logger.info(f"🌡️ Temperature: {temperature}°C, Humidity: {humidity}% from {device_id}")
            
        except Exception as e:
            logger.error(f"Error processing temperature data: {e}")
            
    def _check_critical_conditions_sync(self, pond_id: str, sensor_data: Dict[str, Any]):
        """Check for critical conditions synchronously"""
        try:
            critical_alerts = []
            
            # Critical dissolved oxygen levels
            if sensor_data.get('dissolved_oxygen') is not None:
                do_level = sensor_data['dissolved_oxygen']
                if do_level < 3.0:  # Critical for fish survival
                    critical_alerts.append({
                        'pond_id': pond_id,
                        'alert_type': 'critical_oxygen',
                        'message': f'Dangerously low dissolved oxygen: {do_level} mg/L',
                        'severity': 'critical',
                        'timestamp': datetime.utcnow()
                    })
                elif do_level < 5.0:  # Warning level
                    critical_alerts.append({
                        'pond_id': pond_id,
                        'alert_type': 'low_oxygen',
                        'message': f'Low dissolved oxygen: {do_level} mg/L',
                        'severity': 'high',
                        'timestamp': datetime.utcnow()
                    })
            
            # Critical temperature
            if sensor_data.get('temperature') is not None:
                temp = sensor_data['temperature']
                if temp < 15.0 or temp > 32.0:  # Critical temperature range
                    critical_alerts.append({
                        'pond_id': pond_id,
                        'alert_type': 'temperature_extreme',
                        'message': f'Extreme temperature: {temp}°C',
                        'severity': 'critical',
                        'timestamp': datetime.utcnow()
                    })
            
            # Critical pH levels
            if sensor_data.get('ph') is not None:
                ph = sensor_data['ph']
                if ph < 6.0 or ph > 9.0:  # Critical pH range
                    critical_alerts.append({
                        'pond_id': pond_id,
                        'alert_type': 'ph_extreme',
                        'message': f'Extreme pH level: {ph}',
                        'severity': 'critical',
                        'timestamp': datetime.utcnow()
                    })
            
            # High ammonia levels
            if sensor_data.get('ammonia') is not None:
                ammonia = sensor_data['ammonia']
                if ammonia > 0.5:  # Critical ammonia level
                    critical_alerts.append({
                        'pond_id': pond_id,
                        'alert_type': 'high_ammonia',
                        'message': f'High ammonia level: {ammonia} mg/L',
                        'severity': 'critical',
                        'timestamp': datetime.utcnow()
                    })
            
            # High nitrite levels
            if sensor_data.get('nitrite') is not None:
                nitrite = sensor_data['nitrite']
                if nitrite > 0.5:  # Critical nitrite level
                    critical_alerts.append({
                        'pond_id': pond_id,
                        'alert_type': 'high_nitrite',
                        'message': f'High nitrite level: {nitrite} mg/L',
                        'severity': 'high',
                        'timestamp': datetime.utcnow()
                    })
            
            # Store alerts if any
            if critical_alerts:
                self.sync_db.alerts.insert_many(critical_alerts)
                logger.warning(f"⚠️ Created {len(critical_alerts)} critical alerts for pond {pond_id}")
            
        except Exception as e:
            logger.error(f"Error checking critical conditions: {e}")

    async def process_temperature_data(self, data: Dict[str, Any]):
        """Process temperature sensor data from publisher"""
        try:
            device_id = data.get('device_id', 'unknown')
            temperature = data.get('temperature')
            humidity = data.get('humidity')
            timestamp = data.get('timestamp')
            
            logger.info(f"🌡️ Temperature: {temperature}°C, Humidity: {humidity}% from {device_id}")
            
            # Skip storing incomplete data from random sensors
            # Only log for debugging purposes
            logger.debug(f"Skipping incomplete temperature data from {device_id}")
            
        except Exception as e:
            logger.error(f"Error processing temperature data: {e}")

    async def process_water_quality_data(self, data: Dict[str, Any]):
        """Process comprehensive water quality data"""
        try:
            pond_id = data.get('pond_id', 'unknown')
            device_id = data.get('device_id', 'unknown')
            
            logger.info(f"💧 Water quality data from {device_id} for pond {pond_id}")
            
            # Process this as regular sensor data
            await self.process_sensor_data(pond_id, data)
            
        except Exception as e:
            logger.error(f"Error processing water quality data: {e}")

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
        """Process incoming sensor data with comprehensive validation and storage"""
        try:
            logger.info(f"📊 Processing sensor data for pond {pond_id}: {data}")
            
            # Extract and validate timestamp
            timestamp_str = data.get('timestamp')
            if timestamp_str:
                try:
                    # Handle both ISO format and Unix timestamp
                    if isinstance(timestamp_str, str):
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        timestamp = datetime.fromtimestamp(timestamp_str)
                except (ValueError, TypeError):
                    timestamp = datetime.utcnow()
                    logger.warning(f"Invalid timestamp format for pond {pond_id}, using current time")
            else:
                timestamp = datetime.utcnow()

            # Validate required sensor data
            sensor_values = {
                'temperature': data.get('temperature'),
                'ph': data.get('ph'),
                'dissolved_oxygen': data.get('dissolved_oxygen'),
                'turbidity': data.get('turbidity'),
                'ammonia': data.get('ammonia'),
                'nitrite': data.get('nitrite'),
                'nitrate': data.get('nitrate'),
                'salinity': data.get('salinity'),
                'water_level': data.get('water_level')
            }
            
            # Log data quality
            data_quality = data.get('data_quality', 'unknown')
            sensor_drift = data.get('sensor_drift', 0)
            battery_level = data.get('battery_level', 100)
            
            logger.info(f"🌊 Pond {pond_id} - Quality: {data_quality}, Battery: {battery_level}%, Drift: {sensor_drift}%")
            
            # Validate critical parameters
            validation_errors = []
            if sensor_values['temperature'] is not None:
                if sensor_values['temperature'] < -10 or sensor_values['temperature'] > 50:
                    validation_errors.append(f"Temperature out of range: {sensor_values['temperature']}°C")
            
            if sensor_values['ph'] is not None:
                if sensor_values['ph'] < 0 or sensor_values['ph'] > 14:
                    validation_errors.append(f"pH out of range: {sensor_values['ph']}")
            
            if sensor_values['dissolved_oxygen'] is not None:
                if sensor_values['dissolved_oxygen'] < 0 or sensor_values['dissolved_oxygen'] > 20:
                    validation_errors.append(f"Dissolved oxygen out of range: {sensor_values['dissolved_oxygen']} mg/L")
            
            # Log validation errors but still process data
            if validation_errors:
                logger.warning(f"Validation errors for pond {pond_id}: {validation_errors}")

            # Create sensor reading
            reading_data = SensorReadingCreate(
                pond_id=pond_id,
                timestamp=timestamp,
                temperature=sensor_values['temperature'],
                ph=sensor_values['ph'],
                dissolved_oxygen=sensor_values['dissolved_oxygen'],
                turbidity=sensor_values['turbidity'],
                ammonia=sensor_values['ammonia'],
                nitrite=sensor_values['nitrite'],
                nitrate=sensor_values['nitrate'],
                salinity=sensor_values['salinity'],
                water_level=sensor_values['water_level'],
                device_id=data.get('device_id')
            )

            # Store the reading
            reading = await self.sensor_service.create_reading(reading_data)
            logger.info(f"✅ Stored sensor reading for pond {pond_id} at {timestamp}")

            # Perform anomaly detection
            await self.perform_anomaly_detection(reading)
            
            # Store device metadata if available
            await self.store_device_metadata(pond_id, data)
            
            # Check for critical alerts
            await self.check_critical_conditions(pond_id, sensor_values, data)

        except Exception as e:
            logger.error(f"❌ Error processing sensor data for pond {pond_id}: {e}")
            
    async def store_device_metadata(self, pond_id: str, data: Dict[str, Any]):
        """Store additional device metadata"""
        try:
            device_info = {
                'device_id': data.get('device_id'),
                'battery_level': data.get('battery_level'),
                'signal_strength': data.get('signal_strength'),
                'sensor_status': data.get('sensor_status'),
                'calibration_date': data.get('calibration_date'),
                'data_quality': data.get('data_quality'),
                'sensor_drift': data.get('sensor_drift'),
                'location': data.get('location'),
                'last_seen': datetime.utcnow()
            }
            
            # Here you could store this in a separate device_status collection
            # For now, we'll just log it
            logger.info(f"📱 Device info for pond {pond_id}: {device_info}")
            
        except Exception as e:
            logger.error(f"Error storing device metadata: {e}")
    
    async def check_critical_conditions(self, pond_id: str, sensor_values: Dict[str, Any], data: Dict[str, Any]):
        """Check for critical conditions that need immediate attention"""
        try:
            critical_alerts = []
            
            # Critical dissolved oxygen levels
            if sensor_values.get('dissolved_oxygen') is not None:
                do_level = sensor_values['dissolved_oxygen']
                if do_level < 3.0:  # Critical for fish survival
                    critical_alerts.append({
                        'type': 'critical_oxygen',
                        'message': f'Dangerously low dissolved oxygen: {do_level} mg/L',
                        'severity': 'critical'
                    })
                elif do_level < 5.0:  # Warning level
                    critical_alerts.append({
                        'type': 'low_oxygen',
                        'message': f'Low dissolved oxygen: {do_level} mg/L',
                        'severity': 'high'
                    })
            
            # Critical temperature
            if sensor_values.get('temperature') is not None:
                temp = sensor_values['temperature']
                if temp < 10.0 or temp > 35.0:
                    critical_alerts.append({
                        'type': 'temperature_extreme',
                        'message': f'Extreme temperature: {temp}°C',
                        'severity': 'critical'
                    })
            
            # Critical pH levels
            if sensor_values.get('ph') is not None:
                ph = sensor_values['ph']
                if ph < 6.0 or ph > 9.0:
                    critical_alerts.append({
                        'type': 'ph_extreme',
                        'message': f'Extreme pH level: {ph}',
                        'severity': 'critical'
                    })
            
            # High ammonia levels
            if sensor_values.get('ammonia') is not None:
                ammonia = sensor_values['ammonia']
                if ammonia > 0.25:  # Toxic level
                    critical_alerts.append({
                        'type': 'high_ammonia',
                        'message': f'High ammonia level: {ammonia} mg/L',
                        'severity': 'critical'
                    })
            
            # Low battery warning
            battery_level = data.get('battery_level')
            if battery_level is not None and battery_level < 20:
                critical_alerts.append({
                    'type': 'low_battery',
                    'message': f'Low device battery: {battery_level}%',
                    'severity': 'medium'
                })
            
            # Create alerts for critical conditions
            for alert_info in critical_alerts:
                await self.create_immediate_alert(pond_id, alert_info)
                
        except Exception as e:
            logger.error(f"Error checking critical conditions: {e}")
    
    async def create_immediate_alert(self, pond_id: str, alert_info: Dict[str, Any]):
        """Create immediate alert for critical conditions"""
        try:
            alert_data = AlertCreate(
                pond_id=pond_id,
                alert_type=alert_info['type'],
                severity=alert_info['severity'],
                title=f"Critical Alert - Pond {pond_id}",
                message=alert_info['message']
            )
            
            alert = await self.alert_service.create_alert(alert_data)
            logger.error(f"🚨 CRITICAL ALERT created for pond {pond_id}: {alert_info['message']}")
            
        except Exception as e:
            logger.error(f"Error creating immediate alert: {e}")

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
                pond_id=str(reading.pond_id),  # Convert ObjectId to string
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
