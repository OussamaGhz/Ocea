"""
Simple WebSocket Test Client for MVP Dashboard
"""
import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_websocket():
    """Test WebSocket connection and real-time data"""
    uri = "ws://localhost:8000/mvp/ws"
    
    try:
        logger.info(f"🔌 Connecting to WebSocket: {uri}")
        
        async with websockets.connect(uri) as websocket:
            logger.info("✅ WebSocket connected successfully!")
            logger.info("🎧 Listening for real-time data...")
            logger.info("🛑 Press Ctrl+C to stop\n")
            
            # Listen for messages
            message_count = 0
            async for message in websocket:
                try:
                    data = json.loads(message)
                    message_count += 1
                    
                    logger.info(f"📩 Message #{message_count}")
                    logger.info(f"   Type: {data.get('type', 'unknown')}")
                    
                    if data.get('type') == 'sensor_data':
                        sensor_data = data.get('data', {})
                        logger.info(f"   Pond: {sensor_data.get('pond_id', 'unknown')}")
                        logger.info(f"   pH: {sensor_data.get('ph', 'N/A')}")
                        logger.info(f"   Temp: {sensor_data.get('temperature', 'N/A')}°C")
                        logger.info(f"   DO: {sensor_data.get('dissolved_oxygen', 'N/A')} mg/L")
                        
                    elif data.get('type') == 'alert':
                        alert_data = data.get('data', {})
                        logger.info(f"   🚨 ALERT: {alert_data.get('severity', 'unknown').upper()}")
                        logger.info(f"   Pond: {alert_data.get('pond_id', 'unknown')}")
                        logger.info(f"   Parameter: {alert_data.get('parameter', 'unknown')}")
                        logger.info(f"   Message: {alert_data.get('message', 'No message')}")
                        
                    elif data.get('type') == 'pong':
                        logger.info("   🏓 Pong received - connection alive")
                        
                    logger.info("")  # Empty line for readability
                    
                except json.JSONDecodeError:
                    logger.error(f"❌ Failed to parse message: {message}")
                    
    except websockets.exceptions.ConnectionClosed:
        logger.info("🔌 WebSocket connection closed")
    except ConnectionRefusedError:
        logger.error("❌ Connection refused. Make sure the server is running on localhost:8000")
    except KeyboardInterrupt:
        logger.info("🛑 WebSocket test stopped by user")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")


if __name__ == "__main__":
    print("🌊 MVP WebSocket Test Client")
    print("=" * 40)
    print("This client will connect to your MVP WebSocket endpoint")
    print("and display real-time sensor data and alerts.")
    print("")
    
    try:
        asyncio.run(test_websocket())
    except KeyboardInterrupt:
        print("\n👋 WebSocket test completed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
