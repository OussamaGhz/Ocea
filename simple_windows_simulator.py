#!/usr/bin/env python3
"""
Windows Pond Simulator - Simple and Reliable
Copy this to your Windows machine and run it.
"""

import json
import time
import random
from datetime import datetime, timezone

try:
    import paho.mqtt.client as mqtt
    print("✅ MQTT library loaded")
except ImportError:
    print("❌ Please install: pip install paho-mqtt")
    exit(1)

# Configuration
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "sensors/pond_data"
POND_ID = "pond_001"
DEVICE_ID = "pond_001_sensor_windows"
INTERVAL = 10

class SimplePondSimulator:
    def __init__(self):
        self.connected = False
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        
        # Initial sensor values
        self.sensors = {
            'ph': 7.2,
            'temperature': 25.5,
            'dissolved_oxygen': 6.8,
            'turbidity': 8.2,
            'nitrate': 12.3,
            'nitrite': 0.15,
            'ammonia': 0.08,
            'water_level': 1.8
        }
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print(f"✅ Connected to {BROKER}")
        else:
            print(f"❌ Connection failed: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        print("🔌 Disconnected")
    
    def connect(self):
        print(f"🔄 Connecting to {BROKER}:{PORT}")
        try:
            self.client.connect(BROKER, PORT, 60)
            self.client.loop_start()
            
            # Wait for connection
            for i in range(50):  # 5 seconds timeout
                if self.connected:
                    return True
                time.sleep(0.1)
            
            print("❌ Connection timeout")
            return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def generate_data(self):
        # Small random variations
        for sensor in self.sensors:
            if sensor == 'ph':
                change = random.uniform(-0.05, 0.05)
                self.sensors[sensor] = max(6.5, min(8.5, self.sensors[sensor] + change))
            elif sensor == 'temperature':
                change = random.uniform(-0.3, 0.3)
                self.sensors[sensor] = max(18.0, min(30.0, self.sensors[sensor] + change))
            elif sensor == 'dissolved_oxygen':
                change = random.uniform(-0.2, 0.2)
                self.sensors[sensor] = max(4.0, min(12.0, self.sensors[sensor] + change))
            elif sensor == 'turbidity':
                change = random.uniform(-0.3, 0.3)
                self.sensors[sensor] = max(0.5, min(25.0, self.sensors[sensor] + change))
            elif sensor == 'nitrate':
                change = random.uniform(-0.5, 0.5)
                self.sensors[sensor] = max(0.0, min(40.0, self.sensors[sensor] + change))
            elif sensor in ['nitrite', 'ammonia']:
                change = random.uniform(-0.01, 0.01)
                self.sensors[sensor] = max(0.0, min(0.5, self.sensors[sensor] + change))
            elif sensor == 'water_level':
                change = random.uniform(-0.02, 0.02)
                self.sensors[sensor] = max(0.8, min(2.5, self.sensors[sensor] + change))
        
        data = {
            'pond_id': POND_ID,
            'device_id': DEVICE_ID,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'ph': round(self.sensors['ph'], 2),
            'temperature': round(self.sensors['temperature'], 2),
            'dissolved_oxygen': round(self.sensors['dissolved_oxygen'], 2),
            'turbidity': round(self.sensors['turbidity'], 2),
            'nitrate': round(self.sensors['nitrate'], 2),
            'nitrite': round(self.sensors['nitrite'], 3),
            'ammonia': round(self.sensors['ammonia'], 3),
            'water_level': round(self.sensors['water_level'], 2)
        }
        return data
    
    def publish(self, data):
        if not self.connected:
            print("⚠️ Not connected, skipping...")
            return False
        
        try:
            payload = json.dumps(data)
            result = self.client.publish(TOPIC, payload)
            
            if result.rc == 0:
                print(f"📊 Sent: pH={data['ph']}, Temp={data['temperature']}°C, DO={data['dissolved_oxygen']}mg/L")
                return True
            else:
                print(f"❌ Publish failed: {result.rc}")
                return False
        except Exception as e:
            print(f"❌ Publish error: {e}")
            return False
    
    def run(self):
        print("🌊 Windows Pond Simulator")
        print(f"📡 Broker: {BROKER}:{PORT}")
        print(f"📝 Topic: {TOPIC}")
        print(f"⏱️  Interval: {INTERVAL}s")
        print("=" * 40)
        
        if not self.connect():
            print("❌ Cannot connect. Check network/firewall.")
            return
        
        print("🚀 Simulator started! Press Ctrl+C to stop")
        print()
        
        count = 0
        try:
            while True:
                if self.connected:
                    data = self.generate_data()
                    if self.publish(data):
                        count += 1
                        print(f"   Message #{count} sent ✅")
                else:
                    print("🔄 Reconnecting...")
                    self.connect()
                
                time.sleep(INTERVAL)
        
        except KeyboardInterrupt:
            print("\n🛑 Stopping...")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        finally:
            self.client.loop_stop()
            self.client.disconnect()
            print("✅ Stopped")

if __name__ == "__main__":
    simulator = SimplePondSimulator()
    simulator.run()
