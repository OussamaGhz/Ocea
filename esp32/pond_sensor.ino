/*
 * ESP32 Pond Monitoring Sensor
 * Connects to OCEA MQTT Broker and sends sensor data
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// MQTT Broker settings
const char* mqtt_server = "192.168.1.100";  // Replace with your server IP
const int mqtt_port = 1883;
const char* device_id = "esp32_001";
const char* farm_id = "farm1";
const char* pond_id = "pond1";

// MQTT Topics
String data_topic = String(farm_id) + "/" + String(pond_id) + "/data";
String status_topic = String(farm_id) + "/" + String(pond_id) + "/status";

// Sensor pins
#define TEMP_SENSOR_PIN 4
#define PH_SENSOR_PIN A0
#define DO_SENSOR_PIN A1
#define TURBIDITY_SENSOR_PIN A2

// Temperature sensor setup
OneWire oneWire(TEMP_SENSOR_PIN);
DallasTemperature temperatureSensor(&oneWire);

// WiFi and MQTT clients
WiFiClient espClient;
PubSubClient client(espClient);

// Timing
unsigned long lastMsg = 0;
const long interval = 30000; // Send data every 30 seconds

void setup() {
  Serial.begin(115200);
  
  // Initialize sensors
  temperatureSensor.begin();
  
  // Connect to WiFi
  setup_wifi();
  
  // Setup MQTT
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  
  // Send initial status
  Serial.println("ESP32 Pond Sensor initialized");
}

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  randomSeed(micros());

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println(message);
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    
    // Create a random client ID
    String clientId = "ESP32Client-";
    clientId += String(random(0xffff), HEX);
    
    // Attempt to connect
    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      
      // Send connection status
      publishStatus("online");
      
      // Subscribe to control topics (optional)
      String control_topic = String(farm_id) + "/" + String(pond_id) + "/control";
      client.subscribe(control_topic.c_str());
      
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

float readTemperature() {
  temperatureSensor.requestTemperatures();
  float temp = temperatureSensor.getTempCByIndex(0);
  
  // Add some realistic variation for demo
  temp += random(-100, 100) / 100.0;
  
  return temp;
}

float readPH() {
  // Read analog value and convert to pH
  int sensorValue = analogRead(PH_SENSOR_PIN);
  float voltage = sensorValue * (3.3 / 4095.0);
  
  // Convert voltage to pH (calibration needed for real sensor)
  float ph = 7.0 + (voltage - 1.65) * 2.0;
  
  // Constrain to realistic pH range
  ph = constrain(ph, 6.0, 9.0);
  
  return ph;
}

float readDissolvedOxygen() {
  // Read analog value and convert to DO
  int sensorValue = analogRead(DO_SENSOR_PIN);
  float voltage = sensorValue * (3.3 / 4095.0);
  
  // Convert voltage to DO in mg/L (calibration needed)
  float do_value = voltage * 3.0; // Simplified conversion
  
  // Add realistic variation
  do_value += random(-50, 50) / 100.0;
  
  return constrain(do_value, 0.0, 15.0);
}

float readTurbidity() {
  // Read analog value and convert to NTU
  int sensorValue = analogRead(TURBIDITY_SENSOR_PIN);
  float voltage = sensorValue * (3.3 / 4095.0);
  
  // Convert voltage to turbidity (calibration needed)
  float turbidity = (voltage - 0.3) * 100;
  
  return constrain(turbidity, 0.0, 100.0);
}

void publishSensorData(String sensor_type, float value, String unit) {
  StaticJsonDocument<300> doc;
  
  // Get current timestamp (simplified - in production use NTP)
  unsigned long currentTime = millis();
  
  doc["pond_id"] = pond_id;
  doc["sensor_type"] = sensor_type;
  doc["value"] = value;
  doc["unit"] = unit;
  doc["timestamp"] = String(currentTime); // In production, use proper ISO timestamp
  doc["device_id"] = device_id;
  doc["location"] = "pond_center"; // Optional location info
  
  char buffer[400];
  serializeJson(doc, buffer);
  
  bool published = client.publish(data_topic.c_str(), buffer);
  
  if (published) {
    Serial.print("Published ");
    Serial.print(sensor_type);
    Serial.print(": ");
    Serial.println(value);
  } else {
    Serial.print("Failed to publish ");
    Serial.println(sensor_type);
  }
}

void publishStatus(String status) {
  StaticJsonDocument<200> doc;
  
  doc["device_id"] = device_id;
  doc["status"] = status;
  doc["timestamp"] = String(millis());
  doc["ip_address"] = WiFi.localIP().toString();
  doc["rssi"] = WiFi.RSSI();
  
  char buffer[300];
  serializeJson(doc, buffer);
  
  client.publish(status_topic.c_str(), buffer);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long now = millis();
  if (now - lastMsg > interval) {
    lastMsg = now;
    
    // Read all sensors
    float temperature = readTemperature();
    float ph = readPH();
    float dissolved_oxygen = readDissolvedOxygen();
    float turbidity = readTurbidity();
    
    // Publish sensor data
    publishSensorData("temperature", temperature, "celsius");
    delay(100); // Small delay between publishes
    
    publishSensorData("ph", ph, "pH");
    delay(100);
    
    publishSensorData("dissolved_oxygen", dissolved_oxygen, "mg/L");
    delay(100);
    
    publishSensorData("turbidity", turbidity, "NTU");
    delay(100);
    
    // Print to serial for debugging
    Serial.println("--- Sensor Readings ---");
    Serial.print("Temperature: ");
    Serial.print(temperature);
    Serial.println("°C");
    Serial.print("pH: ");
    Serial.println(ph);
    Serial.print("Dissolved Oxygen: ");
    Serial.print(dissolved_oxygen);
    Serial.println(" mg/L");
    Serial.print("Turbidity: ");
    Serial.print(turbidity);
    Serial.println(" NTU");
    Serial.println("----------------------");
  }
}
