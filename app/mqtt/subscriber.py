#!/usr/bin/env python3
"""
MQTT Subscriber for Pond Monitoring System

This script runs the MQTT subscriber that listens for sensor data
from ESP32 devices and processes them through the anomaly detection system.

Usage:
    python -m app.mqtt.subscriber
"""

import asyncio
import logging
import signal
import sys
from app.config import get_settings
from app.database.connection import connect_to_mongo, close_mongo_connection
from app.mqtt.client import mqtt_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('mqtt_subscriber.log')
    ]
)

logger = logging.getLogger(__name__)
settings = get_settings()

class MQTTSubscriber:
    def __init__(self):
        self.running = False

    async def start(self):
        """Start the MQTT subscriber"""
        logger.info("Starting MQTT Subscriber...")
        
        try:
            # Connect to database
            await connect_to_mongo()
            
            # Initialize MQTT handler
            await mqtt_handler.initialize()
            
            # Setup and connect MQTT client
            mqtt_handler.setup_client()
            
            # Connect to broker in a separate thread
            mqtt_handler.connect()
            
            self.running = True
            logger.info("MQTT Subscriber started successfully")
            
            # Start the MQTT loop in a separate thread
            loop = asyncio.get_event_loop()
            mqtt_task = loop.run_in_executor(None, mqtt_handler.start_loop)
            
            # Keep the main loop running
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error in MQTT subscriber: {e}")
        finally:
            await self.stop()

    async def stop(self):
        """Stop the MQTT subscriber"""
        logger.info("Stopping MQTT Subscriber...")
        self.running = False
        
        # Stop MQTT client
        mqtt_handler.stop()
        
        # Close database connection
        await close_mongo_connection()
        
        logger.info("MQTT Subscriber stopped")

    def signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        logger.info(f"Received signal {signum}")
        self.running = False


async def main():
    """Main function"""
    subscriber = MQTTSubscriber()
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, subscriber.signal_handler)
    signal.signal(signal.SIGTERM, subscriber.signal_handler)
    
    await subscriber.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Subscriber interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
