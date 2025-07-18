# MQTT Integration Guide

## Overview

The system subscribes to MQTT topics in the format: `farm1/{pond_id}/data`

## Message Format

ESP32 devices should publish JSON messages to MQTT with the following structure:

```json
{
  "pond_id": "pond_001",
  "timestamp": "2025-01-18T10:30:00Z",
  "temperature": 25.5,
  "ph": 7.2,
  "dissolved_oxygen": 8.5,
  "turbidity": 12.3,
  "ammonia": 0.1,
  "nitrite": 0.02,
  "nitrate": 15.0,
  "salinity": 0.5,
  "water_level": 120.0
}
```

## Node-RED Integration

### 1. MQTT Input Node Configuration
- **Server**: `localhost:1883` (or your MQTT broker)
- **Topic**: `farm1/+/data`
- **QoS**: 0 or 1
- **Output**: parsed JSON object

### 2. Function Node (Optional Processing)
```javascript
// Add timestamp if not present
if (!msg.payload.timestamp) {
    msg.payload.timestamp = new Date().toISOString();
}

// Validate pond_id
if (!msg.payload.pond_id) {
    // Extract from topic: farm1/pond_001/data
    const topicParts = msg.topic.split('/');
    if (topicParts.length >= 2) {
        msg.payload.pond_id = topicParts[1];
    }
}

return msg;
```

### 3. MQTT Output Node (Forward to Backend)
- **Server**: Backend MQTT broker
- **Topic**: Same as input topic
- **QoS**: 1 (ensure delivery)

## ESP32 Arduino Code Example

```cpp
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// WiFi credentials
const char* ssid = "your_wifi_ssid";
const char* password = "your_wifi_password";

// MQTT configuration
const char* mqtt_server = "your_mqtt_broker";
const int mqtt_port = 1883;
const char* pond_id = "pond_001";

// Sensor pins
#define TEMP_SENSOR_PIN 2
#define PH_SENSOR_PIN A0
#define DO_SENSOR_PIN A1
#define TURBIDITY_SENSOR_PIN A2

// Initialize sensors
OneWire oneWire(TEMP_SENSOR_PIN);
DallasTemperature temperatureSensor(&oneWire);

WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  Serial.begin(115200);
  
  // Initialize sensors
  temperatureSensor.begin();
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected");
  
  // Configure MQTT
  client.setServer(mqtt_server, mqtt_port);
}

void loop() {
  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();
  
  // Read sensors and publish data
  publishSensorData();
  
  // Wait 30 seconds before next reading
  delay(30000);
}

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    String clientId = "ESP32Client-" + String(pond_id);
    
    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void publishSensorData() {
  // Read sensors
  temperatureSensor.requestTemperatures();
  float temperature = temperatureSensor.getTempCByIndex(0);
  float ph = readPHSensor();
  float dissolvedOxygen = readDOSensor();
  float turbidity = readTurbiditySensor();
  
  // Create JSON payload
  StaticJsonDocument<200> doc;
  doc["pond_id"] = pond_id;
  doc["timestamp"] = getTimestamp();
  doc["temperature"] = temperature;
  doc["ph"] = ph;
  doc["dissolved_oxygen"] = dissolvedOxygen;
  doc["turbidity"] = turbidity;
  
  String payload;
  serializeJson(doc, payload);
  
  // Publish to MQTT
  String topic = "farm1/" + String(pond_id) + "/data";
  client.publish(topic.c_str(), payload.c_str());
  
  Serial.println("Published: " + payload);
}

float readPHSensor() {
  // Implement pH sensor reading
  int sensorValue = analogRead(PH_SENSOR_PIN);
  float voltage = sensorValue * (3.3 / 4095.0);
  float ph = 3.3 * voltage; // Calibrate according to your sensor
  return ph;
}

float readDOSensor() {
  // Implement dissolved oxygen sensor reading
  int sensorValue = analogRead(DO_SENSOR_PIN);
  float voltage = sensorValue * (3.3 / 4095.0);
  float do_mg_l = voltage * 4; // Calibrate according to your sensor
  return do_mg_l;
}

float readTurbiditySensor() {
  // Implement turbidity sensor reading
  int sensorValue = analogRead(TURBIDITY_SENSOR_PIN);
  float voltage = sensorValue * (3.3 / 4095.0);
  float turbidity = (voltage - 2.5) * 100; // Calibrate according to your sensor
  return turbidity;
}

String getTimestamp() {
  // In a real implementation, you'd use NTP to get accurate time
  // For now, return a placeholder
  return "2025-01-18T10:30:00Z";
}
```

## Testing MQTT Messages

### Using mosquitto_pub (Command Line)
```bash
mosquitto_pub -h localhost -t "farm1/pond_001/data" -m '{
  "pond_id": "pond_001",
  "timestamp": "2025-01-18T10:30:00Z",
  "temperature": 25.5,
  "ph": 7.2,
  "dissolved_oxygen": 8.5,
  "turbidity": 12.3
}'
```

### Using Python Script
```python
import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime

def publish_test_data():
    client = mqtt.Client()
    client.connect("localhost", 1883, 60)
    
    data = {
        "pond_id": "pond_001",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "temperature": 25.5,
        "ph": 7.2,
        "dissolved_oxygen": 8.5,
        "turbidity": 12.3
    }
    
    topic = "farm1/pond_001/data"
    payload = json.dumps(data)
    
    client.publish(topic, payload)
    client.disconnect()
    
    print(f"Published to {topic}: {payload}")

if __name__ == "__main__":
    publish_test_data()
```

## Sensor Value Ranges

| Parameter | Unit | Normal Range | Critical Low | Critical High |
|-----------|------|--------------|--------------|---------------|
| Temperature | °C | 20-30 | <15 | >35 |
| pH | - | 6.5-8.5 | <6.0 | >9.0 |
| Dissolved Oxygen | mg/L | 5-12 | <3 | >15 |
| Turbidity | NTU | 0-50 | - | >100 |
| Ammonia | mg/L | 0-0.5 | - | >1.0 |
| Nitrite | mg/L | 0-0.1 | - | >0.5 |
| Nitrate | mg/L | 0-40 | - | >80 |
| Salinity | ppt | 0-35 | - | >40 |
| Water Level | cm | 50-200 | <30 | >250 |

## Troubleshooting

### Common Issues

1. **Messages not received by backend**
   - Check MQTT broker connectivity
   - Verify topic format matches `farm1/{pond_id}/data`
   - Ensure JSON payload is valid

2. **Anomaly detection not working**
   - Check if ML model is trained
   - Verify sensor values are within expected ranges
   - Check system logs for errors

3. **Database not updating**
   - Verify MongoDB connection
   - Check for validation errors in logs
   - Ensure proper authentication

### Debug Commands

```bash
# Monitor MQTT messages
mosquitto_sub -h localhost -t "farm1/+/data"

# Check API logs
docker logs pond_api

# Check MQTT subscriber logs
docker logs pond_mqtt_subscriber

# Check database content
mongo pond_monitoring --eval "db.sensor_readings.find().limit(5).pretty()"
```
