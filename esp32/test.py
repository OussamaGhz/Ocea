import json
import time
import threading
import random
import paho.mqtt.client as mqtt

class MQTTConnection:
    def __init__(self, broker_host="192.168.217.25", broker_port=1883, client_id="device_1"):
        """
        Initialize MQTT connection
        
        Args:
            broker_host: MQTT broker IP address (use your PC's IP or public broker)
            broker_port: MQTT broker port (default 1883)
            client_id: Unique identifier for this client
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id
        
        # Fix for paho-mqtt 2.0+ - use the latest callback API version
        try:
            # For paho-mqtt 2.0+ - use VERSION2 (latest)
            self.client = mqtt.Client(client_id=client_id, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        except (TypeError, AttributeError):
            # For older versions of paho-mqtt
            self.client = mqtt.Client(client_id)
        
        # Set up callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
        
        self.is_connected = False
        
    def on_connect(self, client, userdata, flags, reason_code, properties=None):
        """Callback when client connects to broker (VERSION2 compatible)"""
        if reason_code == 0 or str(reason_code) == "Success":
            print(f"✅ Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            self.is_connected = True
            # Subscribe to topics upon successful connection
            self.subscribe_to_topics()
        else:
            print(f"❌ Failed to connect to MQTT broker. Reason code: {reason_code}")
            self.is_connected = False
    
    def on_message(self, client, userdata, msg):
        """Callback when a message is received"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            print(f"📨 Received message on topic '{topic}': {payload}")
            
            # Handle different message types
            if topic == "sensors/temperature":
                self.handle_temperature_data(payload)
            elif topic == "commands/device":
                self.handle_device_command(payload)
            elif topic == "status/heartbeat":
                self.handle_heartbeat(payload)
                
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    def on_disconnect(self, client, userdata, reason_code, properties=None):
        """Callback when client disconnects (VERSION2 compatible)"""
        print(f"🔌 Disconnected from MQTT broker. Reason code: {reason_code}")
        self.is_connected = False
    
    def on_publish(self, client, userdata, mid, reason_code=None, properties=None):
        """Callback when message is published (VERSION2 compatible)"""
        print(f"📤 Message published successfully (ID: {mid})")
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            print(f"🔄 Connecting to MQTT broker at {self.broker_host}:{self.broker_port}...")
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()  # Start network loop in background thread
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()
    
    def subscribe_to_topics(self):
        """Subscribe to relevant topics"""
        topics = [
            ("sensors/temperature", 0),
            ("sensors/humidity", 0),
            ("commands/device", 0),
            ("status/heartbeat", 0)
        ]
        
        for topic, qos in topics:
            self.client.subscribe(topic, qos)
            print(f"🔔 Subscribed to topic: {topic}")
    
    def publish_message(self, topic, payload, qos=0):
        """Publish a message to a topic"""
        if not self.is_connected:
            print("❌ Not connected to broker. Cannot publish message.")
            return False
        
        try:
            # Convert payload to JSON if it's a dict
            if isinstance(payload, dict):
                payload = json.dumps(payload)
            
            result = self.client.publish(topic, payload, qos)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"📤 Published to '{topic}': {payload}")
                return True
            else:
                print(f"❌ Failed to publish message. Error code: {result.rc}")
                return False
        except Exception as e:
            print(f"❌ Error publishing message: {e}")
            return False
    
    def handle_temperature_data(self, payload):
        """Handle temperature sensor data"""
        try:
            data = json.loads(payload)
            temp = data.get('temperature', 'N/A')
            timestamp = data.get('timestamp', time.time())
            print(f"🌡️ Temperature reading: {temp}°C at {timestamp}")
        except:
            print(f"🌡️ Temperature: {payload}")
    
    def handle_device_command(self, payload):
        """Handle device commands"""
        try:
            command = json.loads(payload)
            cmd_type = command.get('command', '')
            
            if cmd_type == 'reboot':
                print("🔄 Received reboot command")
                # Implement reboot logic here
            elif cmd_type == 'status':
                print("📊 Received status request")
                self.send_status_update()
            else:
                print(f"❓ Unknown command: {cmd_type}")
        except:
            print(f"📋 Command: {payload}")
    
    def handle_heartbeat(self, payload):
        """Handle heartbeat messages"""
        print(f"💓 Heartbeat from another device: {payload}")
    
    def send_status_update(self):
        """Send device status update"""
        status = {
            "device_id": self.client_id,
            "status": "online",
            "timestamp": time.time(),
            "uptime": time.time()  # In real scenario, calculate actual uptime
        }
        self.publish_message("status/device", status)
    
    def send_sensor_data(self):
        """Simulate sending sensor data"""
        # Simulate temperature sensor
        temp_data = {
            "temperature": round(random.uniform(20.0, 30.0), 2),
            "humidity": round(random.uniform(40.0, 80.0), 2),
            "timestamp": time.time(),
            "device_id": self.client_id
        }
        
        self.publish_message("sensors/temperature", temp_data)
        
        # Send heartbeat
        heartbeat = {
            "device_id": self.client_id,
            "timestamp": time.time(),
            "status": "alive"
        }
        self.publish_message("status/heartbeat", heartbeat)

def main():
    # Configuration - Try public broker first for testing
    BROKER_HOST = "broker.hivemq.com"  # Public broker for testing
    # Alternative: "test.mosquitto.org" or your local IP if broker is running
    BROKER_PORT = 1883
    CLIENT_ID = "ocea_device_1"
    
    print("🔧 MQTT Configuration:")
    print(f"   Broker: {BROKER_HOST}:{BROKER_PORT}")
    print(f"   Client ID: {CLIENT_ID}")
    print()
    
    # Create MQTT connection
    mqtt_conn = MQTTConnection(BROKER_HOST, BROKER_PORT, CLIENT_ID)
    
    # Connect to broker
    if not mqtt_conn.connect():
        print("❌ Failed to connect to MQTT broker.")
        print("💡 Troubleshooting:")
        print("   1. Check if MQTT broker is running")
        print("   2. Verify the IP address and port")
        print("   3. Check firewall settings")
        print("   4. Try using a public broker: test.mosquitto.org")
        return
    
    # Wait for connection to establish
    time.sleep(2)
    
    try:
        # Send initial status
        mqtt_conn.send_status_update()
        
        # Start periodic sensor data transmission
        print("🚀 Starting sensor data transmission...")
        print("📝 Publishing sensor data every 5 seconds...")
        print("🛑 Press Ctrl+C to stop")
        
        while True:
            if mqtt_conn.is_connected:
                mqtt_conn.send_sensor_data()
            else:
                print("⚠️ Connection lost. Attempting to reconnect...")
                mqtt_conn.connect()
            
            time.sleep(5)  # Send data every 5 seconds
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping MQTT client...")
    except Exception as e:
        print(f"❌ Error in main loop: {e}")
    finally:
        mqtt_conn.disconnect()
        print("👋 MQTT client disconnected")

if __name__ == "__main__":
    main()