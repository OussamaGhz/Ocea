#!/usr/bin/env python3
"""
Pond 002 Simulator

This script simulates sensor data for pond_002 and publishes it to MQTT broker.
The pond simulates sensor readings for:
- pH, Temperature, Dissolved Oxygen, Turbidity, Nitrate, Nitrite, Ammonia, Water Level

Usage:
    python pond_002_simulator.py
"""

import json
import time
import random
import logging
from datetime import datetime, timezone
import paho.mqtt.client as mqtt
from dataclasses import dataclass
from typing import Dict, Any


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class PondConfig:
    """Configuration for pond simulation"""
    pond_id: str = "pond_002"
    device_id: str = "pond_002_sensor"
    
    # MQTT Configuration
    mqtt_broker: str = "broker.hivemq.com"
    mqtt_port: int = 1883
    mqtt_topic: str = "sensors/pond_data"
    
    # Simulation parameters
    publish_interval: int = 12  # seconds (different interval for pond 002)
    
    # Sensor ranges for normal operation (slightly different from pond 001)
    ph_range: tuple = (6.8, 8.2)
    temperature_range: tuple = (20.0, 28.0)  # Celsius
    dissolved_oxygen_range: tuple = (5.0, 11.0)  # mg/L
    turbidity_range: tuple = (1.0, 20.0)  # NTU
    nitrate_range: tuple = (0.0, 35.0)  # mg/L
    nitrite_range: tuple = (0.0, 0.4)  # mg/L
    ammonia_range: tuple = (0.0, 0.4)  # mg/L
    water_level_range: tuple = (1.0, 2.8)  # meters


class PondSimulator:
    """Pond 002 Sensor Data Simulator"""
    
    def __init__(self, config: PondConfig):
        self.config = config
        self.client = mqtt.Client()
        self.is_connected = False
        self.running = False
        
        # Initialize sensor states (to create realistic variations)
        self.sensor_states = {
            'ph': random.uniform(*config.ph_range),
            'temperature': random.uniform(*config.temperature_range),
            'dissolved_oxygen': random.uniform(*config.dissolved_oxygen_range),
            'turbidity': random.uniform(*config.turbidity_range),
            'nitrate': random.uniform(*config.nitrate_range),
            'nitrite': random.uniform(*config.nitrite_range),
            'ammonia': random.uniform(*config.ammonia_range),
            'water_level': random.uniform(*config.water_level_range)
        }
        
        # Set up MQTT callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
    
    def on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.is_connected = True
            logger.info(f"✅ Connected to MQTT broker at {self.config.mqtt_broker}:{self.config.mqtt_port}")
        else:
            logger.error(f"❌ Failed to connect to MQTT broker. Return code: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.is_connected = False
        logger.info(f"🔌 Disconnected from MQTT broker. Return code: {rc}")
    
    def on_publish(self, client, userdata, mid):
        """MQTT publish callback"""
        logger.debug(f"📤 Message published with ID: {mid}")
    
    def generate_sensor_reading(self) -> Dict[str, Any]:
        """Generate realistic sensor reading with gradual changes"""
        
        # Apply small random variations to simulate realistic sensor drift
        for sensor in self.sensor_states:
            config_range = getattr(self.config, f"{sensor}_range")
            min_val, max_val = config_range
            
            # Small random change (-4% to +4% of range for pond 002)
            range_size = max_val - min_val
            change = random.uniform(-0.04 * range_size, 0.04 * range_size)
            
            # Apply change and clamp to valid range
            self.sensor_states[sensor] = max(min_val, min(max_val, self.sensor_states[sensor] + change))
        
        # Create sensor reading
        reading = {
            'pond_id': self.config.pond_id,
            'device_id': self.config.device_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            
            # Core sensor data
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
    
    def publish_reading(self, reading: Dict[str, Any]):
        """Publish sensor reading to MQTT broker"""
        try:
            payload = json.dumps(reading)
            result = self.client.publish(self.config.mqtt_topic, payload)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"📊 Published reading - pH: {reading['ph']}, Temp: {reading['temperature']}°C, DO: {reading['dissolved_oxygen']} mg/L")
            else:
                logger.error(f"❌ Failed to publish reading. Return code: {result.rc}")
                
        except Exception as e:
            logger.error(f"❌ Error publishing reading: {e}")
    
    def connect_to_broker(self) -> bool:
        """Connect to MQTT broker"""
        try:
            logger.info(f"🔄 Connecting to MQTT broker at {self.config.mqtt_broker}:{self.config.mqtt_port}")
            self.client.connect(self.config.mqtt_broker, self.config.mqtt_port, 60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10
            start_time = time.time()
            while not self.is_connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.is_connected:
                logger.info("✅ Connection established successfully!")
                return True
            else:
                logger.error("❌ Connection timeout")
                return False
                
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            return False
    
    def disconnect_from_broker(self):
        """Disconnect from MQTT broker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("👋 Disconnected from MQTT broker")
    
    def run(self):
        """Main simulation loop"""
        logger.info(f"🚀 Starting Pond {self.config.pond_id} Simulator")
        
        if not self.connect_to_broker():
            logger.error("❌ Failed to connect to MQTT broker. Exiting...")
            return
        
        self.running = True
        logger.info(f"📡 Publishing sensor data every {self.config.publish_interval} seconds")
        logger.info("🛑 Press Ctrl+C to stop")
        
        try:
            while self.running:
                if self.is_connected:
                    # Generate and publish sensor reading
                    reading = self.generate_sensor_reading()
                    self.publish_reading(reading)
                else:
                    logger.warning("⚠️ Not connected to MQTT broker, attempting to reconnect...")
                    self.connect_to_broker()
                
                time.sleep(self.config.publish_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Stopping simulation...")
        except Exception as e:
            logger.error(f"❌ Simulation error: {e}")
        finally:
            self.running = False
            self.disconnect_from_broker()
            logger.info("✅ Pond simulator stopped")


def main():
    """Main function"""
    config = PondConfig()
    simulator = PondSimulator(config)
    simulator.run()


if __name__ == "__main__":
    main()
