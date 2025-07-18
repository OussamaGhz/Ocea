/*
 * ESP32 MQTT Test Client - Simple Version
 * Basic connection test without physical sensors
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ========== CONFIGURATION ==========
// WiFi credentials - CHANGE THESE
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// MQTT Broker settings - CHANGE THE IP
const char* mqtt_server = "192.168.1.100";  // Your OCEA server IP address
const int mqtt_port = 1883;

// Device identification - CHANGE IF NEEDED
const char* device_id = "esp32_test_001";
const char* farm_id = "farm1";
const char* pond_id = "pond1";

// ========== TOPICS ==========
String data_topic = String(farm_id) + "/" + String(pond_id) + "/data";
String status_topic = String(farm_id) + "/" + String(pond_id) + "/status";

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastMsg = 0;
const long interval = 10000; // Send test data every 10 seconds

void setup() {
  Serial.begin(115200);
  Serial.println();
  Serial.println("ESP32 MQTT Test Client Starting...");
  
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void setup_wifi() {
  delay(10);
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  Serial.print("Signal strength (RSSI): ");
  Serial.println(WiFi.RSSI());
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message received [");
  Serial.print(topic);
  Serial.print("]: ");
  
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection to ");
    Serial.print(mqtt_server);
    Serial.print(":");
    Serial.print(mqtt_port);
    Serial.print("...");
    
    String clientId = "ESP32-" + String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str())) {
      Serial.println(" connected!");
      
      // Send online status
      publishStatus("online");
      
      // Subscribe to control topic (optional)
      String control_topic = String(farm_id) + "/" + String(pond_id) + "/control";
      client.subscribe(control_topic.c_str());
      Serial.print("Subscribed to: ");
      Serial.println(control_topic);
      
    } else {
      Serial.print(" failed, rc=");
      Serial.print(client.state());
      Serial.println(". Retrying in 5 seconds...");
      
      // Print connection error details
      switch (client.state()) {
        case -4:
          Serial.println("Error: Connection timeout");
          break;
        case -3:
          Serial.println("Error: Connection lost");
          break;
        case -2:
          Serial.println("Error: Connect failed");
          break;
        case -1:
          Serial.println("Error: Disconnected");
          break;
        case 1:
          Serial.println("Error: Wrong protocol");
          break;
        case 2:
          Serial.println("Error: ID rejected");
          break;
        case 3:
          Serial.println("Error: Server unavailable");
          break;
        case 4:
          Serial.println("Error: Bad username/password");
          break;
        case 5:
          Serial.println("Error: Not authorized");
          break;
      }
      
      delay(5000);
    }
  }
}

void publishTestData() {
  // Generate simulated sensor data
  float temperature = 25.0 + random(-50, 50) / 10.0; // 20-30°C
  float ph = 7.0 + random(-10, 10) / 10.0;           // 6-8 pH
  float oxygen = 8.0 + random(-20, 20) / 10.0;       // 6-10 mg/L
  
  // Publish temperature
  publishSensorReading("temperature", temperature, "celsius");
  delay(100);
  
  // Publish pH
  publishSensorReading("ph", ph, "pH");
  delay(100);
  
  // Publish dissolved oxygen
  publishSensorReading("dissolved_oxygen", oxygen, "mg/L");
  delay(100);
}

void publishSensorReading(String sensor_type, float value, String unit) {
  StaticJsonDocument<300> doc;
  
  doc["pond_id"] = pond_id;
  doc["sensor_type"] = sensor_type;
  doc["value"] = value;
  doc["unit"] = unit;
  doc["timestamp"] = "2025-07-18T" + String(millis() / 1000) + "Z"; // Simplified timestamp
  doc["device_id"] = device_id;
  
  char buffer[400];
  serializeJson(doc, buffer);
  
  bool success = client.publish(data_topic.c_str(), buffer);
  
  if (success) {
    Serial.print("✓ Sent ");
    Serial.print(sensor_type);
    Serial.print(": ");
    Serial.print(value);
    Serial.print(" ");
    Serial.println(unit);
  } else {
    Serial.print("✗ Failed to send ");
    Serial.println(sensor_type);
  }
}

void publishStatus(String status) {
  StaticJsonDocument<250> doc;
  
  doc["device_id"] = device_id;
  doc["status"] = status;
  doc["ip_address"] = WiFi.localIP().toString();
  doc["rssi"] = WiFi.RSSI();
  doc["free_heap"] = ESP.getFreeHeap();
  doc["uptime"] = millis();
  
  char buffer[350];
  serializeJson(doc, buffer);
  
  client.publish(status_topic.c_str(), buffer);
  
  Serial.print("Status published: ");
  Serial.println(status);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long now = millis();
  if (now - lastMsg > interval) {
    lastMsg = now;
    
    Serial.println("\n--- Publishing Test Data ---");
    publishTestData();
    Serial.println("--- Data Sent ---\n");
  }
}
