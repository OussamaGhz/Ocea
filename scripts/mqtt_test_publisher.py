#!/usr/bin/env python3
"""
MQTT Test Publisher

This script simulates ESP32 sensor data by publishing test messages to MQTT broker.
Useful for testing the system without actual hardware.
"""

import json
import time
import random
from datetime import datetime, timezone
import paho.mqtt.client as mqtt
from app.config import get_settings

settings = get_settings()


class MQTTTestPublisher:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        
        # Set credentials if provided
        if settings.mqtt_username and settings.mqtt_password:
            self.client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"Connected to MQTT broker at {settings.mqtt_broker_host}:{settings.mqtt_broker_port}")
        else:
            print(f"Failed to connect. Code: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        print("Disconnected from MQTT broker")
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(settings.mqtt_broker_host, settings.mqtt_broker_port, 60)
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def generate_sensor_data(self, pond_id: str, anomaly: bool = False) -> dict:
        """Generate realistic sensor data"""
        if anomaly:
            # Generate anomalous data
            data = {
                "pond_id": pond_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "temperature": random.uniform(35, 40),  # Too high
                "ph": random.uniform(4, 5),  # Too low
                "dissolved_oxygen": random.uniform(1, 3),  # Too low
                "turbidity": random.uniform(80, 120),  # Too high
                "ammonia": random.uniform(1, 2),  # Too high
                "nitrite": random.uniform(0.5, 1),  # Too high
                "nitrate": random.uniform(60, 80),  # Too high
                "salinity": random.uniform(40, 50),  # Too high
                "water_level": random.uniform(20, 40)  # Too low
            }
        else:
            # Generate normal data
            data = {
                "pond_id": pond_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "temperature": random.uniform(22, 28),  # Normal range
                "ph": random.uniform(7, 8),  # Normal range
                "dissolved_oxygen": random.uniform(6, 10),  # Normal range
                "turbidity": random.uniform(5, 25),  # Normal range
                "ammonia": random.uniform(0, 0.3),  # Normal range
                "nitrite": random.uniform(0, 0.05),  # Normal range
                "nitrate": random.uniform(5, 30),  # Normal range
                "salinity": random.uniform(0, 30),  # Normal range
                "water_level": random.uniform(80, 150)  # Normal range
            }
        
        return data
    
    def publish_data(self, pond_id: str, data: dict):
        """Publish sensor data to MQTT"""
        topic = f"farm1/{pond_id}/data"
        payload = json.dumps(data)
        
        result = self.client.publish(topic, payload)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"Published to {topic}: {payload}")
        else:
            print(f"Failed to publish to {topic}")
    
    def run_simulation(self, duration_minutes: int = 60):
        """Run simulation for specified duration"""
        print(f"Starting MQTT simulation for {duration_minutes} minutes...")
        
        if not self.connect():
            return
        
        self.client.loop_start()
        
        ponds = ["pond_001", "pond_002", "pond_003", "pond_004", "pond_005"]
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        try:
            while time.time() < end_time:
                for pond_id in ponds:
                    # 10% chance of generating anomalous data
                    anomaly = random.random() < 0.1
                    
                    data = self.generate_sensor_data(pond_id, anomaly)
                    self.publish_data(pond_id, data)
                    
                    if anomaly:
                        print(f"🚨 Generated anomalous data for {pond_id}")
                
                # Wait before next batch (simulate readings every 30 seconds)
                time.sleep(30)
                
        except KeyboardInterrupt:
            print("\nSimulation interrupted by user")
        finally:
            self.client.loop_stop()
            self.client.disconnect()
            print("Simulation completed")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MQTT Test Publisher for Pond Monitoring")
    parser.add_argument(
        "--duration", 
        type=int, 
        default=60, 
        help="Simulation duration in minutes (default: 60)"
    )
    parser.add_argument(
        "--pond-id", 
        type=str, 
        help="Specific pond ID to simulate (default: simulate all ponds)"
    )
    parser.add_argument(
        "--anomaly", 
        action="store_true", 
        help="Generate only anomalous data"
    )
    
    args = parser.parse_args()
    
    publisher = MQTTTestPublisher()
    
    if args.pond_id:
        # Single pond simulation
        if publisher.connect():
            publisher.client.loop_start()
            try:
                while True:
                    data = publisher.generate_sensor_data(args.pond_id, args.anomaly)
                    publisher.publish_data(args.pond_id, data)
                    time.sleep(10)  # Publish every 10 seconds for single pond
            except KeyboardInterrupt:
                print("\nStopped by user")
            finally:
                publisher.client.loop_stop()
                publisher.client.disconnect()
    else:
        # Multi-pond simulation
        publisher.run_simulation(args.duration)
