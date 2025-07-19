#!/usr/bin/env python3
"""
Simple Pond Simulator for Remote Machine
Copy this entire file to your other Windows machine and run it.
"""

import json
import time
import random
import logging
from datetime import datetime, timezone

# Try to import paho-mqtt
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("❌ paho-mqtt not installed!")
    print("📦 Install it with: pip install paho-mqtt")
    exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MQTT Configuration
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "sensors/pond_data"

# Pond Configuration
POND_ID = "pond_001"
DEVICE_ID = "pond_001_sensor"
PUBLISH_INTERVAL = 10  # seconds

# Sensor ranges
SENSOR_RANGES = {
    'ph': (6.5, 8.5),
    'temperature': (18.0, 30.0),  # Celsius
    'dissolved_oxygen': (4.0, 12.0),  # mg/L
    'turbidity': (0.5, 25.0),  # NTU
    'nitrate': (0.0, 40.0),  # mg/L
    'nitrite': (0.0, 0.5),  # mg/L
    'ammonia': (0.0, 0.5),  # mg/L
    'water_level': (0.8, 2.5)  # meters
}

class SimplePondSimulator:
    """Simple Pond Simulator"""
    
    def __init__(self):
        self.client = mqtt.Client()
        self.is_connected = False
        self.running = False
        
        # Initialize sensor states
        self.sensor_states = {}
        for sensor, (min_val, max_val) in SENSOR_RANGES.items():
            self.sensor_states[sensor] = random.uniform(min_val, max_val)
        
        # MQTT callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
    
    def on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.is_connected = True
            logger.info(f"✅ Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        else:
            logger.error(f"❌ Failed to connect to MQTT broker. Return code: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.is_connected = False
        logger.info(f"🔌 Disconnected from MQTT broker. Return code: {rc}")
    
    def on_publish(self, client, userdata, mid):
        """MQTT publish callback"""
        logger.debug(f"📤 Message published with ID: {mid}")
    
    def generate_sensor_reading(self):
        """Generate realistic sensor reading"""
        # Apply small random variations
        for sensor in self.sensor_states:
            min_val, max_val = SENSOR_RANGES[sensor]
            range_size = max_val - min_val
            change = random.uniform(-0.05 * range_size, 0.05 * range_size)
            self.sensor_states[sensor] = max(min_val, min(max_val, self.sensor_states[sensor] + change))
        
        reading = {
            'pond_id': POND_ID,
            'device_id': DEVICE_ID,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'ph': round(self.sensor_states['ph'], 2),
            'temperature': round(self.sensor_states['temperature'], 2),
            'dissolved_oxygen': round(self.sensor_states['dissolved_oxygen'], 2),
            'turbidity': round(self.sensor_states['turbidity'], 2),
            'nitrate': round(self.sensor_states['nitrate'], 2),
            'nitrite': round(self.sensor_states['nitrite'], 3),
            'ammonia': round(self.sensor_states['ammonia'], 3),
            'water_level': round(self.sensor_states['water_level'], 2)
        }
        
        return reading
    
    def connect_to_broker(self):
        """Connect to MQTT broker"""
        try:
            logger.info(f"🔄 Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10
            start_time = time.time()
            while not self.is_connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.is_connected:
                logger.info("✅ Connection established!")
                return True
            else:
                logger.error("❌ Connection timeout")
                return False
                
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            return False
    
    def run(self):
        """Main simulation loop"""
        logger.info("🚀 Starting Simple Pond Simulator")
        logger.info(f"🔧 Configuration: Broker={MQTT_BROKER}, Port={MQTT_PORT}")
        
        if not self.connect_to_broker():
            logger.error("❌ Failed to connect to MQTT broker. Exiting...")
            return
        
        self.running = True
        logger.info(f"📡 Publishing sensor data every {PUBLISH_INTERVAL} seconds")
        logger.info("🛑 Press Ctrl+C to stop")
        
        try:
            while self.running:
                if self.is_connected:
                    reading = self.generate_sensor_reading()
                    payload = json.dumps(reading)
                    result = self.client.publish(MQTT_TOPIC, payload)
                    
                    if result.rc == mqtt.MQTT_ERR_SUCCESS:
                        logger.info(f"📊 Published: pH={reading['ph']}, Temp={reading['temperature']}°C, DO={reading['dissolved_oxygen']}mg/L")
                    else:
                        logger.error(f"❌ Publish failed. Return code: {result.rc}")
                else:
                    logger.warning("⚠️ Not connected, attempting to reconnect...")
                    self.connect_to_broker()
                
                time.sleep(PUBLISH_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("🛑 Stopping simulation...")
        except Exception as e:
            logger.error(f"❌ Simulation error: {e}")
        finally:
            self.running = False
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("✅ Simulator stopped")

def main():
    """Main function"""
    print("🌊 Simple Pond Simulator")
    print("=" * 30)
    simulator = SimplePondSimulator()
    simulator.run()

if __name__ == "__main__":
    main()
