# Enhanced MQTT Pond Monitoring System

This enhanced version provides realistic pond sensor data simulation and comprehensive backend processing.

## 🔧 Components

### 1. **Enhanced ESP32 Simulator** (`esp32/test.py`)
- **Real pond sensor data**: Temperature, pH, dissolved oxygen, ammonia, nitrite, nitrate, turbidity, salinity, water level
- **Environmental data**: Ambient temperature, humidity, light intensity
- **Device status**: Battery level, signal strength, sensor health
- **Time-based variations**: Day/night cycles affect temperature and dissolved oxygen
- **Realistic value ranges**: Based on actual aquaculture parameters

### 2. **Complete Flow Simulator** (`test_complete_flow.py`)
- **Multiple pond simulation**: 3 different ponds with different fish species
- **Scenario simulation**: Normal, low oxygen, high temperature, pH issues, high ammonia, low battery
- **Realistic timing**: 30-second intervals with problem scenarios every N cycles
- **Comprehensive logging**: Shows what data is being sent

### 3. **Backend Monitor** (`backend_monitor.py`)
- **Data validation**: Checks sensor values against expected ranges
- **Anomaly detection**: Detects unusual patterns in sensor data
- **Critical alerts**: Immediate alerts for dangerous conditions
- **Device health monitoring**: Tracks device status and connectivity
- **Statistics tracking**: Real-time monitoring of system performance

## 🚀 Quick Start

### 1. Run the Enhanced ESP32 Simulator

```bash
cd esp32
python test.py
```

**What it does:**
- Sends realistic pond sensor data every 5 seconds
- Includes all water quality parameters
- Simulates day/night variations
- Publishes to both legacy (`farm1/pond_001/data`) and new (`sensors/water_quality`) topics

### 2. Run the Complete Flow Simulator

```bash
python test_complete_flow.py
```

**What it does:**
- Simulates 3 different ponds
- Runs various scenarios (normal, problematic conditions)
- Shows realistic data flow for 10 minutes
- Demonstrates how alerts would be triggered

### 3. Run the Backend Monitor

```bash
python backend_monitor.py
```

**What it does:**
- Connects to MQTT and processes incoming data
- Validates sensor readings
- Performs anomaly detection
- Creates alerts for critical conditions
- Shows statistics every 30 seconds

## 📊 Data Format Examples

### Water Quality Data (Realistic)
```json
{
  "pond_id": "pond_001",
  "device_id": "pond_001_sensor",
  "timestamp": "2025-01-18T10:30:00Z",
  "location": {
    "latitude": 34.0522,
    "longitude": -118.2437
  },
  "temperature": 24.5,
  "ph": 7.2,
  "dissolved_oxygen": 8.1,
  "turbidity": 2.3,
  "ammonia": 0.08,
  "nitrite": 0.05,
  "nitrate": 12.5,
  "salinity": 1.2,
  "water_level": 1.8,
  "ambient_temperature": 26.0,
  "humidity": 65.5,
  "light_intensity": 75000,
  "battery_level": 87.5,
  "signal_strength": -55,
  "sensor_status": "operational",
  "data_quality": "good",
  "fish_species": "Tilapia"
}
```

### Heartbeat Data
```json
{
  "device_id": "pond_001_sensor",
  "pond_id": "pond_001",
  "timestamp": "2025-01-18T10:30:00Z",
  "status": "alive",
  "uptime": 86400,
  "memory_usage": 45.2,
  "cpu_usage": 23.1,
  "network_quality": "excellent"
}
```

## 🔍 Backend Processing Logic

### 1. **Data Reception**
```python
async def process_pond_data(self, pond_id: str, data: Dict[str, Any]):
    # Extract and validate timestamp
    # Create sensor reading record
    # Validate sensor data
    # Store in database
    # Perform anomaly detection
    # Check critical conditions
    # Log summary
```

### 2. **Anomaly Detection**
- Compares current values with recent historical data
- Calculates deviation scores
- Identifies unusual patterns
- Creates alerts for significant anomalies

### 3. **Critical Condition Monitoring**
```python
# Water quality thresholds
thresholds = {
    'dissolved_oxygen': {'min': 5.0, 'critical_min': 3.0},
    'temperature': {'min': 15.0, 'max': 30.0, 'critical_max': 35.0},
    'ph': {'min': 6.5, 'max': 8.5, 'critical_max': 9.0},
    'ammonia': {'max': 0.25, 'critical_max': 0.5}
}
```

### 4. **Alert Generation**
- **Critical**: Immediate danger to fish (DO < 3mg/L, extreme temperature)
- **High**: Warning conditions (pH out of range, high ammonia)
- **Medium**: System issues (low battery, poor network)
- **Low**: Information alerts

## 🌊 Realistic Scenarios

### Normal Operation
- Temperature: 18-28°C (varies by time of day)
- pH: 6.5-8.5
- Dissolved Oxygen: 5-12 mg/L (higher during day)
- Ammonia: 0-0.15 mg/L
- Battery: 70-100%

### Problem Scenarios
- **Low Oxygen**: DO drops to 1-3.5 mg/L → Critical alert
- **High Temperature**: Temp rises to 32-40°C → Warning alert
- **pH Issues**: pH drops to 5-6 → Critical alert
- **High Ammonia**: NH3 rises to 0.3-0.8 mg/L → Critical alert
- **Low Battery**: Battery drops to 5-15% → Medium alert

## 🔗 MQTT Topics

### Published Topics (ESP32)
- `farm1/{pond_id}/data` - Legacy format for pond data
- `sensors/water_quality` - New format for water quality data
- `status/heartbeat` - Device health status

### Subscribed Topics (Backend)
- `farm1/+/data` - All pond data (legacy)
- `sensors/+` - All sensor data
- `status/+` - All status updates
- `commands/+` - All commands

## 📈 Monitoring Features

### Real-time Statistics
- Total sensor readings processed
- Alerts generated by severity
- Active device count
- Recent alert history

### Device Health Tracking
- Last seen timestamp
- Battery level monitoring
- Signal strength tracking
- Network quality assessment

### Data Quality Validation
- Range checking for all parameters
- Timestamp validation
- Data integrity verification
- Anomaly scoring

## 🚨 Alert Types

### Water Quality Alerts
- `critical_oxygen` - Dangerously low dissolved oxygen
- `temperature_extreme` - Extreme temperature readings
- `ph_extreme` - Dangerous pH levels
- `ammonia_critical` - Toxic ammonia levels

### System Alerts
- `low_battery` - Device battery running low
- `poor_network` - Poor network connectivity
- `device_offline` - Device not responding
- `sensor_drift` - Sensor calibration issues

## 💡 Usage Tips

1. **Start Backend Monitor First**: Run `backend_monitor.py` to see how data is processed
2. **Run Simulators**: Use either `test.py` or `test_complete_flow.py` to generate data
3. **Watch Logs**: Monitor console output to see real-time processing
4. **Check Alerts**: Look for alert messages in the backend monitor
5. **Analyze Statistics**: Statistics are printed every 30 seconds

## 🔧 Configuration

### MQTT Broker
- Default: `broker.hivemq.com:1883` (public broker)
- Change in each script's main() function
- For local testing: use `localhost:1883`

### Monitoring Duration
- ESP32 simulator: Runs until stopped (Ctrl+C)
- Complete flow: 10 minutes by default
- Backend monitor: 10 minutes by default

This enhanced system provides a realistic simulation of pond monitoring with comprehensive data processing and intelligent alerting!
