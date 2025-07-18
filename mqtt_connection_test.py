#!/usr/bin/env python3
"""
Simple MQTT Connection Test

This script tests the MQTT connection with various brokers.
"""

import time
import paho.mqtt.client as mqtt

def test_mqtt_connection():
    """Test MQTT connection to different brokers"""
    
    brokers = [
        ("broker.hivemq.com", 1883),
        ("test.mosquitto.org", 1883),
        ("broker.emqx.io", 1883),
        ("mqtt.eclipseprojects.io", 1883)
    ]
    
    for broker_host, broker_port in brokers:
        print(f"\n🔄 Testing connection to {broker_host}:{broker_port}")
        
        try:
            # Create client
            client = mqtt.Client(client_id=f"test_client_{int(time.time())}")
            
            # Connection flags
            connected = False
            connection_error = None
            
            def on_connect(client, userdata, flags, rc):
                nonlocal connected
                if rc == 0:
                    connected = True
                    print(f"✅ Successfully connected to {broker_host}")
                else:
                    print(f"❌ Failed to connect to {broker_host}. Return code: {rc}")
            
            def on_disconnect(client, userdata, rc):
                print(f"🔌 Disconnected from {broker_host}")
            
            # Set callbacks
            client.on_connect = on_connect
            client.on_disconnect = on_disconnect
            
            # Try to connect
            client.connect(broker_host, broker_port, 60)
            client.loop_start()
            
            # Wait for connection
            start_time = time.time()
            while not connected and (time.time() - start_time) < 10:
                time.sleep(0.1)
            
            if connected:
                print(f"✅ Connection to {broker_host} successful!")
                
                # Test publish
                result = client.publish("test/topic", "Hello World!")
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    print(f"✅ Test message published successfully")
                else:
                    print(f"❌ Failed to publish test message")
                
                # Disconnect
                client.disconnect()
                print(f"👋 Clean disconnect from {broker_host}")
                break
            else:
                print(f"❌ Connection timeout to {broker_host}")
                client.loop_stop()
                
        except Exception as e:
            print(f"❌ Exception connecting to {broker_host}: {e}")
            
        time.sleep(1)  # Brief pause between tests
    
    print("\n🏁 Connection test completed!")

if __name__ == "__main__":
    print("🔧 MQTT Connection Test")
    print("=" * 40)
    test_mqtt_connection()
