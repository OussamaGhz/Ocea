#!/usr/bin/env python3
"""
Complete MQTT Test Script for Pond Monitoring System

This script demonstrates the complete flow:
1. Simulates realistic pond sensor data
2. Publishes to MQTT broker
3. Shows how the backend processes the data
4. Demonstrates alerts and anomaly detection

Usage:
    python test_complete_flow.py
"""

import json
import time
import random
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PondSensorSimulator:
    def __init__(self, broker_host="broker.hivemq.com", broker_port=1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = None
        self.is_connected = False
        self.start_time = time.time()
        self.use_new_callbacks = False  # Initialize callback version flag
        
        # Simulate multiple ponds
        self.ponds = [
            {
                'pond_id': 'pond_001',
                'device_id': 'pond_001_sensor',
                'location': {'latitude': 34.0522, 'longitude': -118.2437},
                'base_temp': 22.0,
                'base_ph': 7.2,
                'base_do': 8.0,
                'fish_species': 'Tilapia'
            },
            {
                'pond_id': 'pond_002', 
                'device_id': 'pond_002_sensor',
                'location': {'latitude': 34.0620, 'longitude': -118.2550},
                'base_temp': 24.0,
                'base_ph': 7.8,
                'base_do': 7.5,
                'fish_species': 'Catfish'
            },
            {
                'pond_id': 'pond_003',
                'device_id': 'pond_003_sensor', 
                'location': {'latitude': 34.0420, 'longitude': -118.2350},
                'base_temp': 26.0,
                'base_ph': 6.8,
                'base_do': 9.0,
                'fish_species': 'Trout'
            }
        ]
        
        self.setup_client()
    
    def setup_client(self):
        """Setup MQTT client"""
        # Use the simple old API for compatibility
        self.client = mqtt.Client(client_id=f"pond_simulator_{int(time.time())}")
        
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected - compatible with old paho-mqtt"""
        if rc == 0:
            print(f"✅ Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            self.is_connected = True
        else:
            print(f"❌ Failed to connect. Reason: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected - compatible with old paho-mqtt"""
        print(f"🔌 Disconnected from MQTT broker")
        self.is_connected = False
    
    def on_publish(self, client, userdata, mid):
        """Callback when message published - compatible with old paho-mqtt"""
        print(f"📤 Message published (ID: {mid})")
    
    def connect(self):
        """Connect to broker"""
        try:
            print(f"🔄 Connecting to {self.broker_host}:{self.broker_port}...")
            
            # Add connection timeout
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            
            # Wait for connection with timeout
            timeout = 10  # seconds
            start_time = time.time()
            while not self.is_connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.is_connected:
                print("✅ Connection established successfully!")
                return True
            else:
                print("❌ Connection timeout - failed to connect within 10 seconds")
                return False
                
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            # Try alternative broker
            print("🔄 Trying alternative broker: test.mosquitto.org...")
            try:
                self.broker_host = "test.mosquitto.org"
                self.client.connect(self.broker_host, self.broker_port, 60)
                self.client.loop_start()
                
                start_time = time.time()
                while not self.is_connected and (time.time() - start_time) < timeout:
                    time.sleep(0.1)
                
                if self.is_connected:
                    print("✅ Connected to alternative broker!")
                    return True
                else:
                    print("❌ Alternative broker also failed")
                    return False
            except Exception as e2:
                print(f"❌ Alternative broker also failed: {e2}")
                return False
    
    def disconnect(self):
        """Disconnect from broker"""
        self.client.loop_stop()
        self.client.disconnect()
    
    def generate_realistic_data(self, pond_info, scenario="normal"):
        """Generate realistic sensor data for a pond"""
        current_time = datetime.utcnow()
        hour = current_time.hour
        
        # Base values from pond configuration
        base_temp = pond_info['base_temp']
        base_ph = pond_info['base_ph']
        base_do = pond_info['base_do']
        
        # Time-based variations
        if 6 <= hour <= 18:  # Daytime
            temp_variation = random.uniform(2.0, 4.0)
            do_variation = random.uniform(0.5, 1.5)
            light_intensity = random.uniform(50000, 100000)
        else:  # Nighttime
            temp_variation = random.uniform(-2.0, -0.5)
            do_variation = random.uniform(-1.0, -0.3)
            light_intensity = random.uniform(0, 1000)
        
        # Generate data based on scenario
        if scenario == "normal":
            data = {
                "pond_id": pond_info['pond_id'],
                "device_id": pond_info['device_id'],
                "timestamp": current_time.isoformat() + 'Z',
                "location": pond_info['location'],
                
                # Water quality parameters
                "temperature": round(base_temp + temp_variation + random.uniform(-1.0, 1.0), 2),
                "ph": round(base_ph + random.uniform(-0.3, 0.3), 2),
                "dissolved_oxygen": round(max(0, base_do + do_variation + random.uniform(-0.5, 0.5)), 2),
                "turbidity": round(random.uniform(1.0, 8.0), 2),
                "ammonia": round(random.uniform(0.0, 0.15), 3),
                "nitrite": round(random.uniform(0.0, 0.1), 3),
                "nitrate": round(random.uniform(5.0, 20.0), 2),
                "salinity": round(random.uniform(0.0, 3.0), 2),
                "water_level": round(random.uniform(1.2, 2.0), 2),
                
                # Environmental data
                "ambient_temperature": round(base_temp + temp_variation + random.uniform(-2.0, 2.0), 2),
                "humidity": round(random.uniform(45.0, 85.0), 2),
                "light_intensity": round(light_intensity, 0),
                
                # System status
                "battery_level": round(random.uniform(70.0, 100.0), 1),
                "signal_strength": round(random.uniform(-70, -40), 0),
                "sensor_status": "operational",
                "calibration_date": "2025-01-15T08:00:00Z",
                "data_quality": "good",
                "sensor_drift": round(random.uniform(0.0, 2.0), 2),
                "measurement_count": random.randint(5, 10),
                
                # Fish species info
                "fish_species": pond_info['fish_species']
            }
        
        elif scenario == "low_oxygen":
            data = self.generate_realistic_data(pond_info, "normal")
            data["dissolved_oxygen"] = round(random.uniform(1.0, 3.5), 2)  # Critical level
            data["data_quality"] = "warning"
        
        elif scenario == "high_temperature":
            data = self.generate_realistic_data(pond_info, "normal")
            data["temperature"] = round(random.uniform(32.0, 40.0), 2)  # Too hot
            data["data_quality"] = "warning"
        
        elif scenario == "ph_extreme":
            data = self.generate_realistic_data(pond_info, "normal")
            data["ph"] = round(random.uniform(5.0, 6.0), 2)  # Too acidic
            data["data_quality"] = "warning"
        
        elif scenario == "high_ammonia":
            data = self.generate_realistic_data(pond_info, "normal")
            data["ammonia"] = round(random.uniform(0.3, 0.8), 3)  # Toxic level
            data["data_quality"] = "critical"
        
        elif scenario == "low_battery":
            data = self.generate_realistic_data(pond_info, "normal")
            data["battery_level"] = round(random.uniform(5.0, 15.0), 1)  # Low battery
            data["signal_strength"] = round(random.uniform(-95, -80), 0)  # Weak signal
        
        return data
    
    def publish_pond_data(self, pond_info, scenario="normal"):
        """Publish data for a specific pond"""
        if not self.is_connected:
            return False
        
        data = self.generate_realistic_data(pond_info, scenario)
        
        # Publish to multiple topics for compatibility
        topics = [
            f"farm1/{pond_info['pond_id']}/data",  # Legacy format
            "sensors/water_quality",  # New format
        ]
        
        for topic in topics:
            try:
                payload = json.dumps(data, indent=2)
                result = self.client.publish(topic, payload, qos=0)
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    print(f"📊 Published {scenario} data for {pond_info['pond_id']} to {topic}")
                    print(f"   Temp: {data['temperature']}°C, DO: {data['dissolved_oxygen']}mg/L, pH: {data['ph']}")
                else:
                    print(f"❌ Failed to publish to {topic}")
            except Exception as e:
                print(f"❌ Error publishing to {topic}: {e}")
        
        return True
    
    def run_simulation(self, duration_minutes=10):
        """Run the complete simulation"""
        print(f"🚀 Starting pond monitoring simulation for {duration_minutes} minutes...")
        print(f"📊 Monitoring {len(self.ponds)} ponds")
        
        end_time = time.time() + (duration_minutes * 60)
        cycle_count = 0
        
        try:
            while time.time() < end_time:
                cycle_count += 1
                print(f"\n🔄 Cycle {cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
                
                for i, pond in enumerate(self.ponds):
                    # Determine scenario based on cycle and pond
                    if cycle_count % 20 == 0 and i == 0:  # Every 20 cycles, pond 1 has low oxygen
                        scenario = "low_oxygen"
                    elif cycle_count % 25 == 0 and i == 1:  # Every 25 cycles, pond 2 has high temp
                        scenario = "high_temperature"
                    elif cycle_count % 30 == 0 and i == 2:  # Every 30 cycles, pond 3 has pH issues
                        scenario = "ph_extreme"
                    elif cycle_count % 50 == 0:  # Every 50 cycles, simulate high ammonia
                        scenario = "high_ammonia"
                    elif cycle_count % 100 == 0:  # Every 100 cycles, simulate low battery
                        scenario = "low_battery"
                    else:
                        scenario = "normal"
                    
                    self.publish_pond_data(pond, scenario)
                    time.sleep(1)  # Small delay between ponds
                
                # Send heartbeat for each device
                for pond in self.ponds:
                    heartbeat = {
                        "device_id": pond['device_id'],
                        "pond_id": pond['pond_id'],
                        "timestamp": datetime.utcnow().isoformat() + 'Z',
                        "status": "alive",
                        "uptime": round(time.time() - self.start_time, 2),
                        "memory_usage": round(random.uniform(30.0, 60.0), 1),
                        "cpu_usage": round(random.uniform(10.0, 30.0), 1),
                        "network_quality": random.choice(["excellent", "good", "fair"]),
                        "last_maintenance": "2025-01-10T14:30:00Z"
                    }
                    
                    self.client.publish("status/heartbeat", json.dumps(heartbeat))
                
                print(f"⏱️ Waiting 30 seconds before next cycle...")
                time.sleep(1)  # Wait 30 seconds between cycles
                
        except KeyboardInterrupt:
            print("\n🛑 Simulation stopped by user")
        
        print(f"\n✅ Simulation completed after {cycle_count} cycles")

def main():
    """Main function to run the simulation"""
    print("🏊 Pond Monitoring System - Complete Flow Simulation")
    print("=" * 60)
    
    # Configuration
    BROKER_HOST = "broker.hivemq.com"  # Use public broker for testing
    BROKER_PORT = 1883
    
    print(f"📡 MQTT Broker: {BROKER_HOST}:{BROKER_PORT}")
    print(f"🔧 This simulation will:")
    print(f"   • Simulate 3 fish ponds with different characteristics")
    print(f"   • Generate realistic sensor data every 30 seconds")
    print(f"   • Include normal and problematic scenarios")
    print(f"   • Show how alerts would be triggered")
    print()
    
    # Create simulator
    simulator = PondSensorSimulator(BROKER_HOST, BROKER_PORT)
    
    # Connect to broker
    if not simulator.connect():
        print("❌ Failed to connect to MQTT broker")
        return
    
    try:
        # Run simulation
        simulator.run_simulation(duration_minutes=10)
    finally:
        simulator.disconnect()
        print("👋 Disconnected from MQTT broker")

if __name__ == "__main__":
    main()
