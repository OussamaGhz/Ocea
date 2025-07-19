#!/usr/bin/env python3
"""
MQTT Connection Diagnostic Tool
Copy this to your other machine to diagnose connection issues
"""

import socket
import paho.mqtt.client as mqtt
import time
import sys

def test_dns_resolution():
    """Test if we can resolve the broker hostname"""
    try:
        broker = "broker.hivemq.com"
        ip = socket.gethostbyname(broker)
        print(f"✅ DNS Resolution: {broker} -> {ip}")
        return True, ip
    except Exception as e:
        print(f"❌ DNS Resolution failed: {e}")
        return False, None

def test_socket_connection(host, port):
    """Test raw socket connection to broker"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Socket connection to {host}:{port} successful")
            return True
        else:
            print(f"❌ Socket connection failed with code: {result}")
            return False
    except Exception as e:
        print(f"❌ Socket connection error: {e}")
        return False

def test_mqtt_connection():
    """Test MQTT client connection"""
    broker = "broker.hivemq.com"
    port = 1883
    connected = False
    
    def on_connect(client, userdata, flags, rc):
        nonlocal connected
        if rc == 0:
            connected = True
            print(f"✅ MQTT connection successful")
        else:
            print(f"❌ MQTT connection failed with code: {rc}")
    
    def on_disconnect(client, userdata, rc):
        print(f"🔌 MQTT disconnected with code: {rc}")
    
    try:
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        
        print(f"🔄 Attempting MQTT connection to {broker}:{port}")
        client.connect(broker, port, 60)
        client.loop_start()
        
        # Wait for connection
        timeout = 15
        start_time = time.time()
        while not connected and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        client.loop_stop()
        client.disconnect()
        
        return connected
        
    except Exception as e:
        print(f"❌ MQTT connection error: {e}")
        return False

def test_alternative_brokers():
    """Test connection to alternative public MQTT brokers"""
    brokers = [
        ("test.mosquitto.org", 1883),
        ("mqtt.eclipse.org", 1883),
        ("broker.emqx.io", 1883)
    ]
    
    print("\n🔄 Testing alternative brokers:")
    for broker, port in brokers:
        print(f"\nTesting {broker}:{port}")
        if test_socket_connection(broker, port):
            return broker, port
    
    return None, None

def main():
    """Run all diagnostic tests"""
    print("🔧 MQTT Connection Diagnostic Tool")
    print("=" * 50)
    
    # Test 1: DNS Resolution
    print("\n1. Testing DNS Resolution:")
    dns_ok, ip = test_dns_resolution()
    
    # Test 2: Socket Connection
    print("\n2. Testing Socket Connection:")
    if dns_ok:
        socket_ok = test_socket_connection("broker.hivemq.com", 1883)
    else:
        socket_ok = False
    
    # Test 3: MQTT Connection
    print("\n3. Testing MQTT Connection:")
    if socket_ok:
        mqtt_ok = test_mqtt_connection()
    else:
        mqtt_ok = False
    
    # Test 4: Network diagnostics
    print("\n4. Network Information:")
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"   Local hostname: {hostname}")
        print(f"   Local IP: {local_ip}")
    except:
        print("   Could not get local network info")
    
    # Test 5: Alternative brokers if main one fails
    if not mqtt_ok:
        print("\n5. Testing Alternative Brokers:")
        alt_broker, alt_port = test_alternative_brokers()
        if alt_broker:
            print(f"\n✅ Alternative broker found: {alt_broker}:{alt_port}")
            print(f"   You can use this broker instead of broker.hivemq.com")
        else:
            print("\n❌ No alternative brokers accessible")
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 DIAGNOSTIC SUMMARY:")
    print(f"   DNS Resolution: {'✅ OK' if dns_ok else '❌ FAILED'}")
    print(f"   Socket Connection: {'✅ OK' if socket_ok else '❌ FAILED'}")
    print(f"   MQTT Connection: {'✅ OK' if mqtt_ok else '❌ FAILED'}")
    
    if mqtt_ok:
        print("\n🎉 Your connection should work fine!")
        print("   The issue might be with the simulator file on your other machine.")
        print("   Make sure you're using the updated version.")
    else:
        print("\n⚠️  Connection issues detected!")
        if not dns_ok:
            print("   - DNS resolution failed (check internet connection)")
        elif not socket_ok:
            print("   - Socket connection failed (firewall/network issue)")
        else:
            print("   - MQTT protocol issue")
        
        print("\n💡 RECOMMENDATIONS:")
        print("   1. Check your internet connection")
        print("   2. Check if a firewall is blocking port 1883")
        print("   3. Try running from a different network")
        print("   4. Contact your network administrator")

if __name__ == "__main__":
    main()
