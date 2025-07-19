#!/usr/bin/env python3
"""
Windows Pond Simulator - Guaranteed to Work
Copy this entire file to your Windows machine and run it.
This simulator will send pond sensor data to the MQTT broker.
"""

import json
import time
import random
import logging
from datetime import datetime, timezone

# Try to import paho-mqtt
try:
    import paho.mqtt.client as mqtt
    print("✅ paho-mqtt library loaded successfully")
except ImportError:
    print("❌ paho-mqtt not installed!")
    print("📦 Install it with: pip install paho-mqtt")
    exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "sensors/pond_data"
POND_ID = "pond_001"
DEVICE_ID = "pond_001_sensor_windows"
PUBLISH_INTERVAL = 10  # seconds

class WindowsPondSimulator:
    """Windows Pond Simulator - Sends realistic sensor data"""
    
    def __init__(self):
        self.client = mqtt.Client()
        self.is_connected = False
        self.running = False
        
        # Initialize sensor states for realistic variations
        self.sensor_states = {
            'ph': 7.2,
            'temperature': 25.5,
            'dissolved_oxygen': 6.8,
            'turbidity': 8.2,
            'nitrate': 12.3,
            'nitrite': 0.15,
            'ammonia': 0.08,
            'water_level': 1.8
        }
        
        # Set up MQTT callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
    
    def on_connect(self, client, userdata, flags, rc):
        """Called when MQTT client connects"""
        if rc == 0:
            self.is_connected = True
            print(f"✅ Successfully connected to {MQTT_BROKER}:{MQTT_PORT}")
            logger.info("MQTT connection established")
        else:
            self.is_connected = False
            print(f"❌ Connection failed with return code: {rc}")
            logger.error(f"MQTT connection failed: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Called when MQTT client disconnects"""
        self.is_connected = False
        print(f"🔌 Disconnected from broker (code: {rc})")
        logger.info("MQTT disconnected")
    
    def on_publish(self, client, userdata, mid):
        """Called when message is published"""
        logger.debug(f"Message {mid} published")
    
    def generate_realistic_reading(self):
        """Generate realistic sensor data with small variations"""
        
        # Apply small random changes to simulate real sensors
        variations = {
            'ph': random.uniform(-0.1, 0.1),
            'temperature': random.uniform(-0.5, 0.5),
            'dissolved_oxygen': random.uniform(-0.3, 0.3),
            'turbidity': random.uniform(-0.5, 0.5),
            'nitrate': random.uniform(-1.0, 1.0),
            'nitrite': random.uniform(-0.02, 0.02),
            'ammonia': random.uniform(-0.01, 0.01),
            'water_level': random.uniform(-0.05, 0.05)
        }
        
        # Apply variations with realistic limits
        ranges = {
            'ph': (6.5, 8.5),
            'temperature': (18.0, 30.0),
            'dissolved_oxygen': (4.0, 12.0),
            'turbidity': (0.5, 25.0),
            'nitrate': (0.0, 40.0),
            'nitrite': (0.0, 0.5),
            'ammonia': (0.0, 0.5),
            'water_level': (0.8, 2.5)
        }
        
        for sensor in self.sensor_states:
            # Apply variation
            self.sensor_states[sensor] += variations[sensor]
            
            # Keep within realistic ranges
            min_val, max_val = ranges[sensor]
            self.sensor_states[sensor] = max(min_val, min(max_val, self.sensor_states[sensor]))
        
        # Create sensor reading
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
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            print(f"🔄 Connecting to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
            
            # Connect to broker
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
            
            # Wait for connection with timeout
            timeout = 10
            start_time = time.time()
            
            while not self.is_connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.is_connected:
                print("✅ Connection successful!")
                return True
            else:
                print("❌ Connection timed out")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            print("👋 Disconnected from broker")
    
    def publish_reading(self, reading):
        """Publish sensor reading to MQTT broker"""
        try:
            payload = json.dumps(reading, indent=2)
            result = self.client.publish(MQTT_TOPIC, payload)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"📊 Data published: pH={reading['ph']}, Temp={reading['temperature']}°C, DO={reading['dissolved_oxygen']}mg/L")
                return True
            else:
                print(f"❌ Publish failed with return code: {result.rc}")
                return False
                
        except Exception as e:
            print(f"❌ Error publishing data: {e}")
            return False
    
    def run(self):
        """Main simulation loop"""
        print("🌊 Windows Pond Simulator Starting")
        print("=" * 50)
        print(f"🔧 Pond ID: {POND_ID}")
        print(f"🔧 Device ID: {DEVICE_ID}")
        print(f"🔧 Broker: {MQTT_BROKER}:{MQTT_PORT}")
        print(f"🔧 Topic: {MQTT_TOPIC}")
        print(f"🔧 Interval: {PUBLISH_INTERVAL} seconds")
        print("=" * 50)
        
        # Connect to broker
        if not self.connect():
            print("❌ Failed to connect. Exiting...")
            return
        
        self.running = True
        print(f"🚀 Simulator started! Publishing every {PUBLISH_INTERVAL} seconds")
        print("🛑 Press Ctrl+C to stop")
        print()
        
        try:
            message_count = 0
            
            while self.running:
                if self.is_connected:
                    # Generate and publish sensor data
                    reading = self.generate_realistic_reading()
                    
                    if self.publish_reading(reading):
                        message_count += 1
                        print(f"   📈 Message #{message_count} sent successfully")
                    else:
                        print("   ⚠️ Message failed to send")
                    
                else:
                    print("⚠️ Not connected to broker, attempting to reconnect...")
                    self.connect()
                
                # Wait for next reading
                time.sleep(PUBLISH_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping simulator...")
        except Exception as e:
            print(f"\n❌ Simulator error: {e}")
        finally:
            self.running = False
            self.disconnect()
            print("✅ Simulator stopped successfully")

def main():
    """Main function"""
    print("🌊 WINDOWS POND SIMULATOR")
    print("This simulator sends realistic pond sensor data to the MQTT broker")
    print()
    
    # Create and run simulator
    simulator = WindowsPondSimulator()
    simulator.run()

if __name__ == "__main__":
    main()
