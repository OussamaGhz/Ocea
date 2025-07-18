import paho.mqtt.client as mqtt
import json
import time
import threading

class MQTTConnection:
    def __init__(self, broker_host="localhost", broker_port=1883, client_id="device_1"):
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
        self.client = mqtt.Client(client_id)
        
        # Set up callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
        
        self.is_connected = False
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback when client connects to broker"""
        if rc == 0:
            print(f"✅ Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            self.is_connected = True
            # Subscribe to topics upon successful connection
            self.subscribe_to_topics()
        else:
            print(f"❌ Failed to connect to MQTT broker. Return code: {rc}")
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
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when client disconnects"""
        print(f"🔌 Disconnected from MQTT broker. Return code: {rc}")
        self.is_connected = False
    
    def on_publish(self, client, userdata, mid):
        """Callback when message is published"""
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
        import random
        
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
    # Configuration
    BROKER_HOST = "localhost"  # Change to your broker's IP address
    BROKER_PORT = 1883
    CLIENT_ID = "ocea_device_1"
    
    # Create MQTT connection
    mqtt_conn = MQTTConnection(BROKER_HOST, BROKER_PORT, CLIENT_ID)
    
    # Connect to broker
    if not mqtt_conn.connect():
        print("❌ Failed to connect to MQTT broker. Exiting...")
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