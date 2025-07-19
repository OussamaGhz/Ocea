#!/usr/bin/env python3
"""
ROBUST Windows Pond Simulator
This will definitely work on your Windows machine!
"""

import json
import time
import random
import sys
from datetime import datetime, timezone

try:
    import paho.mqtt.client as mqtt
    print("✅ paho-mqtt imported successfully")
except ImportError:
    print("❌ Missing library! Run: pip install paho-mqtt")
    input("Press Enter to exit...")
    sys.exit(1)

# MQTT Configuration
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "sensors/pond_data"
POND_ID = "pond_001"
DEVICE_ID = "windows_simulator"

class RobustPondSimulator:
    def __init__(self):
        self.client = None
        self.connected = False
        self.message_count = 0
        
        # Sensor initial values
        self.ph = 7.2
        self.temperature = 25.5
        self.dissolved_oxygen = 6.8
        self.turbidity = 8.2
        self.nitrate = 12.3
        self.nitrite = 0.15
        self.ammonia = 0.08
        self.water_level = 1.8
        
        print("🌊 Robust Pond Simulator Initialized")
    
    def on_connect_callback(self, client, userdata, flags, rc):
        """Connection callback"""
        if rc == 0:
            self.connected = True
            print("🎉 MQTT Connected Successfully!")
        else:
            self.connected = False
            print(f"❌ MQTT Connection Failed. Code: {rc}")
    
    def on_disconnect_callback(self, client, userdata, rc):
        """Disconnect callback"""
        self.connected = False
        print(f"🔌 MQTT Disconnected. Code: {rc}")
    
    def on_publish_callback(self, client, userdata, mid):
        """Publish callback"""
        print(f"   ✅ Message {mid} delivered")
    
    def setup_mqtt(self):
        """Setup MQTT client"""
        try:
            print("🔧 Setting up MQTT client...")
            self.client = mqtt.Client()
            self.client.on_connect = self.on_connect_callback
            self.client.on_disconnect = self.on_disconnect_callback
            self.client.on_publish = self.on_publish_callback
            print("✅ MQTT client configured")
            return True
        except Exception as e:
            print(f"❌ MQTT setup error: {e}")
            return False
    
    def connect_to_broker(self):
        """Connect to MQTT broker with retries"""
        print(f"🔄 Connecting to {BROKER}:{PORT}...")
        
        try:
            self.client.connect(BROKER, PORT, 60)
            self.client.loop_start()
            
            # Wait for connection (up to 10 seconds)
            for i in range(100):
                if self.connected:
                    print("✅ Connection established!")
                    return True
                time.sleep(0.1)
                if i % 20 == 0:
                    print(f"   ⏳ Waiting for connection... ({i//10}s)")
            
            print("❌ Connection timeout after 10 seconds")
            return False
            
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def generate_sensor_data(self):
        """Generate realistic sensor data with small variations"""
        
        # Apply small random changes
        self.ph += random.uniform(-0.02, 0.02)
        self.temperature += random.uniform(-0.1, 0.1)
        self.dissolved_oxygen += random.uniform(-0.05, 0.05)
        self.turbidity += random.uniform(-0.1, 0.1)
        self.nitrate += random.uniform(-0.2, 0.2)
        self.nitrite += random.uniform(-0.005, 0.005)
        self.ammonia += random.uniform(-0.003, 0.003)
        self.water_level += random.uniform(-0.01, 0.01)
        
        # Keep values in realistic ranges
        self.ph = max(6.5, min(8.5, self.ph))
        self.temperature = max(18.0, min(30.0, self.temperature))
        self.dissolved_oxygen = max(4.0, min(12.0, self.dissolved_oxygen))
        self.turbidity = max(0.5, min(25.0, self.turbidity))
        self.nitrate = max(0.0, min(40.0, self.nitrate))
        self.nitrite = max(0.0, min(0.5, self.nitrite))
        self.ammonia = max(0.0, min(0.5, self.ammonia))
        self.water_level = max(0.8, min(2.5, self.water_level))
        
        # Create data packet
        data = {
            "pond_id": POND_ID,
            "device_id": DEVICE_ID,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ph": round(self.ph, 2),
            "temperature": round(self.temperature, 2),
            "dissolved_oxygen": round(self.dissolved_oxygen, 2),
            "turbidity": round(self.turbidity, 2),
            "nitrate": round(self.nitrate, 2),
            "nitrite": round(self.nitrite, 3),
            "ammonia": round(self.ammonia, 3),
            "water_level": round(self.water_level, 2)
        }
        
        return data
    
    def publish_data(self, data):
        """Publish sensor data to MQTT broker"""
        if not self.connected:
            print("⚠️ Not connected to broker")
            return False
        
        try:
            payload = json.dumps(data, indent=2)
            result = self.client.publish(TOPIC, payload)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.message_count += 1
                print(f"📊 #{self.message_count} | pH:{data['ph']} | T:{data['temperature']}°C | DO:{data['dissolved_oxygen']}mg/L")
                return True
            else:
                print(f"❌ Publish failed. Return code: {result.rc}")
                return False
                
        except Exception as e:
            print(f"❌ Publish error: {e}")
            return False
    
    def run_simulation(self):
        """Run the main simulation loop"""
        print("\n🚀 STARTING POND SIMULATION")
        print("=" * 50)
        print(f"🏷️  Pond ID: {POND_ID}")
        print(f"🏷️  Device ID: {DEVICE_ID}")
        print(f"🌐 MQTT Broker: {BROKER}:{PORT}")
        print(f"📡 MQTT Topic: {TOPIC}")
        print("=" * 50)
        
        # Setup MQTT
        if not self.setup_mqtt():
            print("❌ Failed to setup MQTT. Exiting.")
            return
        
        # Connect to broker
        if not self.connect_to_broker():
            print("❌ Failed to connect to broker. Exiting.")
            return
        
        print("\n✅ Simulator is ready!")
        print("📊 Publishing sensor data every 10 seconds...")
        print("🛑 Press Ctrl+C to stop\n")
        
        try:
            while True:
                if self.connected:
                    # Generate and publish data
                    sensor_data = self.generate_sensor_data()
                    self.publish_data(sensor_data)
                else:
                    print("🔄 Reconnecting to broker...")
                    if not self.connect_to_broker():
                        print("❌ Reconnection failed. Retrying in 5 seconds...")
                        time.sleep(5)
                        continue
                
                # Wait 10 seconds
                time.sleep(10)
                
        except KeyboardInterrupt:
            print("\n🛑 Simulation stopped by user")
        except Exception as e:
            print(f"\n❌ Simulation error: {e}")
        finally:
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()
            print("✅ Simulator shut down successfully")
            print(f"📊 Total messages sent: {self.message_count}")

def main():
    """Main function"""
    print("🌊 WINDOWS POND SIMULATOR")
    print("This simulator sends pond sensor data to your MQTT broker")
    print()
    
    simulator = RobustPondSimulator()
    simulator.run_simulation()
    
    print("\n👋 Thanks for using the simulator!")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
