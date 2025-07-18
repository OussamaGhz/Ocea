#!/usr/bin/env python3
"""
Backend MQTT Monitor with Real Database Integration

This script demonstrates the backend processing of MQTT data
with real MongoDB database storage.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import paho.mqtt.client as mqtt
from pymongo import MongoClient
from bson import ObjectId

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BackendMonitor:
    def __init__(self, broker_host="broker.hivemq.com", broker_port=1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = None
        self.is_connected = False
        
        # MongoDB connection
        self.mongo_client = None
        self.db = None
        self.sensor_collection = None
        
        # In-memory storage for demonstration
        self.data_store = []  # Simulate database
        self.alerts = []      # Simulate alerts collection
        self.device_status = {}  # Track device status
        
        self.setup_database()
        self.setup_mqtt()
    
    def setup_database(self):
        """Setup MongoDB connection"""
        try:
            # Connect to MongoDB
            self.mongo_client = MongoClient('mongodb://localhost:27017/')
            self.db = self.mongo_client['ocea']
            self.sensor_collection = self.db['sensor_readings']
            logger.info("✅ Connected to MongoDB database")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            self.mongo_client = None
    
    def setup_mqtt(self):
        """Setup MQTT client"""
        self.setup_client()
    
    def setup_client(self):
        """Setup MQTT client"""
        # Use the simple old API for compatibility
        self.client = mqtt.Client(client_id=f"backend_monitor_{int(datetime.now().timestamp())}")
        
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker - compatible with old paho-mqtt"""
        if rc == 0:
            logger.info(f"✅ Backend connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            self.is_connected = True
            self.subscribe_to_topics()
        else:
            logger.error(f"❌ Failed to connect to MQTT broker. Reason: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected - compatible with old paho-mqtt"""
        logger.info(f"🔌 Backend disconnected from MQTT broker")
        self.is_connected = False
    
    def subscribe_to_topics(self):
        """Subscribe to all relevant topics"""
        topics = [
            ("farm1/+/data", 0),        # Legacy pond data
            ("sensors/water_quality", 0), # New water quality format
            ("sensors/+", 0),           # All sensor data
            ("status/+", 0),            # Device status
            ("commands/+", 0)           # Commands
        ]
        
        for topic, qos in topics:
            self.client.subscribe(topic, qos)
            logger.info(f"🔔 Subscribed to topic: {topic}")
    
    def on_message(self, client, userdata, msg):
        """Process incoming MQTT messages"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            # Skip empty or invalid messages
            if not payload or len(payload) < 2:
                return
                
            data = json.loads(payload)
            
            logger.info(f"📨 Received message on topic '{topic}'")
            
            # Route message based on topic - run synchronously to avoid event loop issues
            if topic.startswith("farm1/") and topic.endswith("/data"):
                # Legacy pond data format
                pond_id = topic.split('/')[1]
                # Run synchronously
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Create a task if loop is running
                        asyncio.create_task(self.process_pond_data(pond_id, data))
                    else:
                        # Run synchronously if no loop is running
                        loop.run_until_complete(self.process_pond_data(pond_id, data))
                except RuntimeError:
                    # No event loop, create a new one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.process_pond_data(pond_id, data))
                    loop.close()
            
            elif topic == "sensors/water_quality":
                # New water quality format
                pond_id = data.get('pond_id', 'unknown')
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self.process_pond_data(pond_id, data))
                    else:
                        loop.run_until_complete(self.process_pond_data(pond_id, data))
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.process_pond_data(pond_id, data))
                    loop.close()
            
            elif topic.startswith("sensors/"):
                # Other sensor data - handle synchronously
                self.process_sensor_data_sync(topic, data)
            
            elif topic.startswith("status/"):
                # Device status updates - handle synchronously
                self.process_status_update_sync(topic, data)
            
            elif topic.startswith("commands/"):
                # Device commands - handle synchronously
                self.process_command_sync(topic, data)
            
        except json.JSONDecodeError as e:
            # Skip invalid JSON from other clients on public broker
            if "pond" in topic.lower() or "farm" in topic.lower():
                logger.error(f"❌ Failed to parse JSON payload from {topic}: {e}")
        except Exception as e:
            logger.error(f"❌ Error processing MQTT message: {e}")
    
    async def process_pond_data(self, pond_id: str, data: Dict[str, Any]):
        """Process comprehensive pond sensor data"""
        try:
            logger.info(f"🏊 Processing pond data for {pond_id}")
            
            # Extract timestamp
            timestamp_str = data.get('timestamp')
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.utcnow()
            
            # Create sensor reading record
            sensor_reading = {
                'id': f"reading_{len(self.data_store) + 1}",
                'pond_id': pond_id,
                'device_id': data.get('device_id'),
                'timestamp': timestamp,
                'temperature': data.get('temperature'),
                'ph': data.get('ph'),
                'dissolved_oxygen': data.get('dissolved_oxygen'),
                'turbidity': data.get('turbidity'),
                'ammonia': data.get('ammonia'),
                'nitrite': data.get('nitrite'),
                'nitrate': data.get('nitrate'),
                'salinity': data.get('salinity'),
                'water_level': data.get('water_level'),
                'data_quality': data.get('data_quality', 'good'),
                'battery_level': data.get('battery_level'),
                'signal_strength': data.get('signal_strength'),
                'location': data.get('location'),
                'fish_species': data.get('fish_species'),
                'created_at': datetime.utcnow()
            }
            
            # Validate data
            validation_errors = self.validate_sensor_data(sensor_reading)
            if validation_errors:
                logger.warning(f"⚠️ Validation errors for {pond_id}: {validation_errors}")
                sensor_reading['validation_errors'] = validation_errors
            
            # Store in simulated database
            self.data_store.append(sensor_reading)
            logger.info(f"💾 Stored sensor reading #{sensor_reading['id']} for pond {pond_id}")
            
            # Store in real MongoDB database
            if self.mongo_client is not None and self.sensor_collection is not None:
                try:
                    # Convert datetime objects to ISO strings for MongoDB
                    mongo_record = {
                        'pond_id': pond_id,
                        'device_id': sensor_reading.get('device_id'),
                        'timestamp': sensor_reading['timestamp'],
                        'temperature': sensor_reading.get('temperature'),
                        'ph': sensor_reading.get('ph'),
                        'dissolved_oxygen': sensor_reading.get('dissolved_oxygen'),
                        'turbidity': sensor_reading.get('turbidity'),
                        'ammonia': sensor_reading.get('ammonia'),
                        'nitrite': sensor_reading.get('nitrite'),
                        'nitrate': sensor_reading.get('nitrate'),
                        'salinity': sensor_reading.get('salinity'),
                        'water_level': sensor_reading.get('water_level'),
                        'data_quality': sensor_reading.get('data_quality'),
                        'battery_level': sensor_reading.get('battery_level'),
                        'signal_strength': sensor_reading.get('signal_strength'),
                        'location': sensor_reading.get('location'),
                        'fish_species': sensor_reading.get('fish_species'),
                        'created_at': sensor_reading['created_at']
                    }
                    
                    result = self.sensor_collection.insert_one(mongo_record)
                    logger.info(f"🗄️ Stored in MongoDB with ID: {result.inserted_id}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to store in MongoDB: {e}")
            else:
                logger.warning("⚠️ MongoDB not available, storing only in memory")
            
            # Perform anomaly detection
            await self.perform_anomaly_detection(sensor_reading)
            
            # Check for critical conditions
            await self.check_critical_conditions(sensor_reading)
            
            # Log data summary
            self.log_data_summary(sensor_reading)
            
        except Exception as e:
            logger.error(f"❌ Error processing pond data for {pond_id}: {e}")
    
    def process_sensor_data_sync(self, topic: str, data: Dict[str, Any]):
        """Process other sensor data synchronously"""
        try:
            sensor_type = topic.split('/')[-1]
            device_id = data.get('device_id', 'unknown')
            
            logger.info(f"📡 Processing {sensor_type} data from {device_id}")
            
            # For temperature sensors, check if it's too extreme
            if sensor_type == 'temperature':
                temp = data.get('temperature')
                if temp and (temp < 0 or temp > 50):
                    logger.warning(f"⚠️ Extreme temperature reading: {temp}°C from {device_id}")
            
        except Exception as e:
            logger.error(f"❌ Error processing sensor data: {e}")
    
    def process_status_update_sync(self, topic: str, data: Dict[str, Any]):
        """Process device status updates synchronously"""
        try:
            status_type = topic.split('/')[-1]
            device_id = data.get('device_id', 'unknown')
            
            # Update device status
            self.device_status[device_id] = {
                'last_seen': datetime.utcnow(),
                'status': data.get('status', 'unknown'),
                'uptime': data.get('uptime'),
                'memory_usage': data.get('memory_usage'),
                'cpu_usage': data.get('cpu_usage'),
                'network_quality': data.get('network_quality')
            }
            
            logger.info(f"📊 Updated status for {device_id}: {data.get('status', 'unknown')}")
            
        except Exception as e:
            logger.error(f"❌ Error processing status update: {e}")
    
    def process_command_sync(self, topic: str, data: Dict[str, Any]):
        """Process device commands synchronously"""
        try:
            command_type = topic.split('/')[-1]
            logger.info(f"📋 Processing command: {command_type} - {data}")
            
        except Exception as e:
            logger.error(f"❌ Error processing command: {e}")
    
    async def process_sensor_data(self, topic: str, data: Dict[str, Any]):
        """Process other sensor data"""
        try:
            sensor_type = topic.split('/')[-1]
            device_id = data.get('device_id', 'unknown')
            
            logger.info(f"📡 Processing {sensor_type} data from {device_id}")
            
            # Store sensor data
            sensor_data = {
                'topic': topic,
                'sensor_type': sensor_type,
                'device_id': device_id,
                'data': data,
                'timestamp': datetime.utcnow()
            }
            
            # For temperature sensors, check if it's too extreme
            if sensor_type == 'temperature':
                temp = data.get('temperature')
                if temp and (temp < 0 or temp > 50):
                    await self.create_alert(device_id, 'temperature_extreme', 
                                          f'Extreme temperature reading: {temp}°C', 'high')
            
        except Exception as e:
            logger.error(f"❌ Error processing sensor data: {e}")
    
    async def process_status_update(self, topic: str, data: Dict[str, Any]):
        """Process device status updates"""
        try:
            status_type = topic.split('/')[-1]
            device_id = data.get('device_id', 'unknown')
            
            # Update device status
            self.device_status[device_id] = {
                'last_seen': datetime.utcnow(),
                'status': data.get('status', 'unknown'),
                'uptime': data.get('uptime'),
                'memory_usage': data.get('memory_usage'),
                'cpu_usage': data.get('cpu_usage'),
                'network_quality': data.get('network_quality')
            }
            
            logger.info(f"📊 Updated status for {device_id}: {data.get('status', 'unknown')}")
            
            # Check for device issues
            if status_type == 'heartbeat':
                await self.check_device_health(device_id, data)
            
        except Exception as e:
            logger.error(f"❌ Error processing status update: {e}")
    
    async def process_command(self, topic: str, data: Dict[str, Any]):
        """Process device commands"""
        try:
            command_type = topic.split('/')[-1]
            logger.info(f"📋 Processing command: {command_type} - {data}")
            
            # Log command for audit trail
            command_log = {
                'topic': topic,
                'command_type': command_type,
                'data': data,
                'timestamp': datetime.utcnow()
            }
            
            # In a real system, you might store commands in database
            logger.info(f"📝 Command logged: {command_log}")
            
        except Exception as e:
            logger.error(f"❌ Error processing command: {e}")
    
    def validate_sensor_data(self, reading: Dict[str, Any]) -> List[str]:
        """Validate sensor data against expected ranges"""
        errors = []
        
        # Check temperature
        temp = reading.get('temperature')
        if temp is not None:
            if temp < -20 or temp > 60:
                errors.append(f"Temperature out of expected range: {temp}°C")
        
        # Check pH
        ph = reading.get('ph')
        if ph is not None:
            if ph < 0 or ph > 14:
                errors.append(f"pH out of valid range: {ph}")
        
        # Check dissolved oxygen
        do = reading.get('dissolved_oxygen')
        if do is not None:
            if do < 0 or do > 25:
                errors.append(f"Dissolved oxygen out of expected range: {do} mg/L")
        
        # Check ammonia
        ammonia = reading.get('ammonia')
        if ammonia is not None:
            if ammonia < 0 or ammonia > 2:
                errors.append(f"Ammonia out of expected range: {ammonia} mg/L")
        
        return errors
    
    async def perform_anomaly_detection(self, reading: Dict[str, Any]):
        """Simulate anomaly detection"""
        try:
            pond_id = reading['pond_id']
            anomaly_score = 0.0
            reasons = []
            
            # Simple anomaly detection logic
            # In a real system, this would use ML models
            
            # Check against recent historical data
            recent_readings = []
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            for r in self.data_store:
                if r['pond_id'] == pond_id:
                    # Handle both naive and aware datetimes
                    reading_time = r['timestamp']
                    if hasattr(reading_time, 'tzinfo') and reading_time.tzinfo is not None:
                        # Convert aware datetime to naive for comparison
                        reading_time = reading_time.replace(tzinfo=None)
                    if reading_time > cutoff_time:
                        recent_readings.append(r)
            
            if len(recent_readings) >= 5:
                # Calculate averages
                avg_temp = sum(r['temperature'] for r in recent_readings[-5:] if r['temperature']) / 5
                avg_ph = sum(r['ph'] for r in recent_readings[-5:] if r['ph']) / 5
                avg_do = sum(r['dissolved_oxygen'] for r in recent_readings[-5:] if r['dissolved_oxygen']) / 5
                
                # Check for significant deviations
                if reading['temperature'] and abs(reading['temperature'] - avg_temp) > 5:
                    anomaly_score += 0.3
                    reasons.append(f"Temperature deviation: {reading['temperature']}°C vs avg {avg_temp:.1f}°C")
                
                if reading['ph'] and abs(reading['ph'] - avg_ph) > 1:
                    anomaly_score += 0.4
                    reasons.append(f"pH deviation: {reading['ph']} vs avg {avg_ph:.1f}")
                
                if reading['dissolved_oxygen'] and abs(reading['dissolved_oxygen'] - avg_do) > 3:
                    anomaly_score += 0.5
                    reasons.append(f"DO deviation: {reading['dissolved_oxygen']} mg/L vs avg {avg_do:.1f} mg/L")
            
            # Update reading with anomaly info
            reading['is_anomaly'] = anomaly_score > 0.5
            reading['anomaly_score'] = anomaly_score
            reading['anomaly_reasons'] = reasons
            
            if reading['is_anomaly']:
                logger.warning(f"🔍 Anomaly detected for pond {pond_id}: Score={anomaly_score:.2f}, Reasons={reasons}")
                await self.create_alert(pond_id, 'anomaly', f"Anomaly detected: {', '.join(reasons)}", 'medium')
            
        except Exception as e:
            logger.error(f"❌ Error in anomaly detection: {e}")
    
    async def check_critical_conditions(self, reading: Dict[str, Any]):
        """Check for critical water quality conditions"""
        try:
            pond_id = reading['pond_id']
            alerts = []
            
            # Check dissolved oxygen
            do = reading.get('dissolved_oxygen')
            if do is not None:
                if do < self.thresholds['dissolved_oxygen']['critical_min']:
                    alerts.append(('critical_oxygen', f'Critical low dissolved oxygen: {do} mg/L', 'critical'))
                elif do < self.thresholds['dissolved_oxygen']['min']:
                    alerts.append(('low_oxygen', f'Low dissolved oxygen: {do} mg/L', 'high'))
            
            # Check temperature
            temp = reading.get('temperature')
            if temp is not None:
                if temp < self.thresholds['temperature']['critical_min'] or temp > self.thresholds['temperature']['critical_max']:
                    alerts.append(('temperature_extreme', f'Extreme temperature: {temp}°C', 'critical'))
                elif temp < self.thresholds['temperature']['min'] or temp > self.thresholds['temperature']['max']:
                    alerts.append(('temperature_warning', f'Temperature out of range: {temp}°C', 'high'))
            
            # Check pH
            ph = reading.get('ph')
            if ph is not None:
                if ph < self.thresholds['ph']['critical_min'] or ph > self.thresholds['ph']['critical_max']:
                    alerts.append(('ph_extreme', f'Extreme pH level: {ph}', 'critical'))
                elif ph < self.thresholds['ph']['min'] or ph > self.thresholds['ph']['max']:
                    alerts.append(('ph_warning', f'pH out of optimal range: {ph}', 'high'))
            
            # Check ammonia
            ammonia = reading.get('ammonia')
            if ammonia is not None:
                if ammonia > self.thresholds['ammonia']['critical_max']:
                    alerts.append(('ammonia_critical', f'Critical ammonia level: {ammonia} mg/L', 'critical'))
                elif ammonia > self.thresholds['ammonia']['max']:
                    alerts.append(('ammonia_high', f'High ammonia level: {ammonia} mg/L', 'high'))
            
            # Check battery level
            battery = reading.get('battery_level')
            if battery is not None and battery < 15:
                alerts.append(('low_battery', f'Low device battery: {battery}%', 'medium'))
            
            # Create alerts
            for alert_type, message, severity in alerts:
                await self.create_alert(pond_id, alert_type, message, severity)
            
        except Exception as e:
            logger.error(f"❌ Error checking critical conditions: {e}")
    
    async def check_device_health(self, device_id: str, heartbeat_data: Dict[str, Any]):
        """Check device health from heartbeat"""
        try:
            # Check memory usage
            memory_usage = heartbeat_data.get('memory_usage')
            if memory_usage and memory_usage > 90:
                await self.create_alert(device_id, 'high_memory', f'High memory usage: {memory_usage}%', 'medium')
            
            # Check network quality
            network_quality = heartbeat_data.get('network_quality')
            if network_quality == 'poor':
                await self.create_alert(device_id, 'poor_network', 'Poor network quality detected', 'medium')
            
            logger.info(f"💓 Device {device_id} health check completed")
            
        except Exception as e:
            logger.error(f"❌ Error checking device health: {e}")
    
    async def create_alert(self, pond_id: str, alert_type: str, message: str, severity: str):
        """Create an alert"""
        try:
            alert = {
                'id': f"alert_{len(self.alerts) + 1}",
                'pond_id': pond_id,
                'alert_type': alert_type,
                'severity': severity,
                'title': f"Alert - Pond {pond_id}",
                'message': message,
                'timestamp': datetime.utcnow(),
                'status': 'active'
            }
            
            self.alerts.append(alert)
            
            # Log alert with appropriate emoji
            emoji = {'critical': '🚨', 'high': '⚠️', 'medium': '📢', 'low': '📝'}
            logger.warning(f"{emoji.get(severity, '📢')} {severity.upper()} ALERT: {message}")
            
        except Exception as e:
            logger.error(f"❌ Error creating alert: {e}")
    
    def log_data_summary(self, reading: Dict[str, Any]):
        """Log summary of sensor data"""
        try:
            pond_id = reading['pond_id']
            temp = reading.get('temperature', 'N/A')
            ph = reading.get('ph', 'N/A')
            do = reading.get('dissolved_oxygen', 'N/A')
            ammonia = reading.get('ammonia', 'N/A')
            battery = reading.get('battery_level', 'N/A')
            
            logger.info(f"📊 POND {pond_id} Summary: Temp={temp}°C, pH={ph}, DO={do}mg/L, NH3={ammonia}mg/L, Battery={battery}%")
            
        except Exception as e:
            logger.error(f"❌ Error logging data summary: {e}")
    
    def print_statistics(self):
        """Print system statistics"""
        try:
            total_readings = len(self.data_store)
            total_alerts = len(self.alerts)
            active_devices = len(self.device_status)
            
            # Count alerts by severity
            alert_counts = {}
            for alert in self.alerts:
                severity = alert['severity']
                alert_counts[severity] = alert_counts.get(severity, 0) + 1
            
            print(f"\n📈 SYSTEM STATISTICS:")
            print(f"   Total sensor readings: {total_readings}")
            print(f"   Total alerts generated: {total_alerts}")
            print(f"   Active devices: {active_devices}")
            print(f"   Alerts by severity: {alert_counts}")
            
            # Show recent alerts
            recent_alerts = [a for a in self.alerts if a['timestamp'] > datetime.utcnow() - timedelta(minutes=5)]
            if recent_alerts:
                print(f"\n🔔 RECENT ALERTS (last 5 minutes):")
                for alert in recent_alerts[-5:]:
                    print(f"   • {alert['severity'].upper()}: {alert['message']}")
            
        except Exception as e:
            logger.error(f"❌ Error printing statistics: {e}")
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            logger.info(f"🔄 Connecting to MQTT broker at {self.broker_host}:{self.broker_port}")
            
            # Add connection timeout
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            
            # Wait for connection with timeout
            timeout = 10  # seconds
            start_time = time.time()
            while not self.is_connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.is_connected:
                logger.info("✅ Connection established successfully!")
                return True
            else:
                logger.error("❌ Connection timeout - failed to connect within 10 seconds")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to MQTT broker: {e}")
            # Try alternative broker
            logger.info("🔄 Trying alternative broker: test.mosquitto.org...")
            try:
                self.broker_host = "test.mosquitto.org"
                self.client.connect(self.broker_host, self.broker_port, 60)
                self.client.loop_start()
                
                start_time = time.time()
                while not self.is_connected and (time.time() - start_time) < timeout:
                    time.sleep(0.1)
                
                if self.is_connected:
                    logger.info("✅ Connected to alternative broker!")
                    return True
                else:
                    logger.error("❌ Alternative broker also failed")
                    return False
            except Exception as e2:
                logger.error(f"❌ Alternative broker also failed: {e2}")
                return False
    
    def disconnect(self):
        """Disconnect from MQTT broker and close database connections"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("� Disconnected from MQTT broker")
        
        if self.mongo_client:
            self.mongo_client.close()
            logger.info("🗄️ Closed MongoDB connection")
        
        logger.info("👋 Backend monitor stopped")

async def main():
    """Main function"""
    print("🖥️ Backend Data Processing Monitor")
    print("=" * 50)
    
    # Create backend monitor
    monitor = BackendMonitor()
    
    # Connect to MQTT
    if not monitor.connect():
        print("❌ Failed to connect to MQTT broker")
        return
    
    try:
        logger.info("🎯 Backend monitor started - waiting for MQTT data...")
        logger.info("📡 Subscribed to topics: farm1/+/data, sensors/+, status/+")
        
        # Run for specified time
        run_time = 600  # 10 minutes
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < run_time:
            await asyncio.sleep(30)  # Wait 30 seconds
            monitor.print_statistics()
            
            # Check for offline devices
            current_time = datetime.utcnow()
            for device_id, status in monitor.device_status.items():
                last_seen = status['last_seen']
                if (current_time - last_seen).seconds > 120:  # 2 minutes
                    logger.warning(f"⚠️ Device {device_id} may be offline - last seen {last_seen}")
    
    except KeyboardInterrupt:
        logger.info("🛑 Backend monitor stopped by user")
    finally:
        monitor.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
