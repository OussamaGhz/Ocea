# ESP32 MQTT Configuration Guide

## 🔧 Required Information for ESP32

### 1. Network Configuration
```cpp
// WiFi Settings
const char* ssid = "YOUR_WIFI_SSID";           // Your WiFi network name
const char* password = "YOUR_WIFI_PASSWORD";   // Your WiFi password

// MQTT Broker Settings
const char* mqtt_server = "192.168.1.100";     // Your OCEA server IP address
const int mqtt_port = 1883;                    // MQTT port (from mosquitto.conf)
```

### 2. Device Identification
```cpp
const char* device_id = "esp32_001";    // Unique device identifier
const char* farm_id = "farm1";          // Farm ID (must match your OCEA farm)
const char* pond_id = "pond1";          // Pond ID (must match your OCEA pond)
```

## 🌐 How to Find Your Server IP Address

### Option 1: If OCEA is running locally
```bash
# On your OCEA server, run:
ip addr show | grep inet
# or
hostname -I
```

### Option 2: If OCEA is on another machine
```bash
# From your ESP32 development machine:
ping your-server-hostname
# or check your router's admin panel for connected devices
```

### Option 3: For testing on same network
- If your OCEA server is on `192.168.1.100`, use that IP
- If it's on `192.168.0.50`, use that IP
- Check your router admin panel (usually `192.168.1.1` or `192.168.0.1`)

## 📡 MQTT Topics Used

Your ESP32 will publish to these topics:
```
farm1/pond1/data     - Sensor readings
farm1/pond1/status   - Device status updates
```

And can subscribe to:
```
farm1/pond1/control  - Control commands (optional)
```

## 🔌 Required Arduino Libraries

Install these libraries in Arduino IDE:
```
1. WiFi (ESP32 built-in)
2. PubSubClient by Nick O'Leary
3. ArduinoJson by Benoit Blanchon
4. OneWire by Jim Studt (for temperature sensors)
5. DallasTemperature by Miles Burton (for DS18B20)
```

## 📋 Installation Steps

1. **Install Arduino IDE** and ESP32 board support
2. **Install required libraries** (Tools → Manage Libraries)
3. **Copy the code** (`simple_test.ino` for testing, `pond_sensor.ino` for full sensors)
4. **Configure your settings**:
   - WiFi SSID and password
   - MQTT server IP address
   - Device, farm, and pond IDs
5. **Upload to ESP32**
6. **Open Serial Monitor** (115200 baud) to see connection status

## 🧪 Testing Steps

### 1. Start with Simple Test
- Use `simple_test.ino` first
- Check serial monitor for connection messages
- Verify data appears in your OCEA system

### 2. Check MQTT Connection
```bash
# On your OCEA server, monitor MQTT messages:
docker exec -it pond_mosquitto mosquitto_sub -h localhost -t "farm1/pond1/data"
```

### 3. Verify in OCEA Dashboard
- Go to `http://your-server-ip:8000/docs`
- Check sensor data endpoints
- View real-time data in the API

## 🔧 Troubleshooting

### WiFi Connection Issues
- Check SSID and password spelling
- Ensure 2.4GHz network (ESP32 doesn't support 5GHz)
- Check signal strength

### MQTT Connection Issues
- Verify server IP address
- Check if MQTT broker is running: `docker ps | grep mosquitto`
- Test broker connectivity: `telnet your-server-ip 1883`

### No Data in OCEA
- Check topic names match your farm/pond IDs
- Verify JSON format in serial monitor
- Check OCEA API logs for errors

## 📊 Expected Serial Output

```
ESP32 MQTT Test Client Starting...
Connecting to WiFi: MyWiFiNetwork
...
WiFi connected!
IP address: 192.168.1.105
Attempting MQTT connection to 192.168.1.100:1883... connected!
Status published: online
Subscribed to: farm1/pond1/control

--- Publishing Test Data ---
✓ Sent temperature: 26.3 celsius
✓ Sent ph: 7.2 pH
✓ Sent dissolved_oxygen: 8.7 mg/L
--- Data Sent ---
```

## 🌟 Production Considerations

1. **Security**: Enable MQTT authentication for production
2. **Timestamps**: Use NTP for accurate timestamps
3. **Error Handling**: Add reconnection logic and data buffering
4. **Power Management**: Implement deep sleep for battery operation
5. **OTA Updates**: Add over-the-air update capability

## 📝 Sensor Connections (for full version)

```
DS18B20 Temperature Sensor:
- VCC → 3.3V
- GND → GND  
- Data → GPIO 4

pH Sensor:
- VCC → 3.3V
- GND → GND
- Analog Out → A0

Dissolved Oxygen Sensor:
- VCC → 3.3V
- GND → GND
- Analog Out → A1
```

## 🔗 Integration with OCEA

Your ESP32 data will automatically:
- Appear in OCEA database
- Trigger anomaly detection
- Be available via REST API
- Work with Node-RED flows
- Generate alerts if values are out of range
