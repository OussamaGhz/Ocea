# Dashboard API Documentation

This document outlines the comprehensive dashboard API routes that integrate MQTT subscriber data with pond management for real-time monitoring and analytics.

## 🌊 Dashboard API Endpoints

### Base URL: `http://localhost:8080/dashboard`

### Authentication Required
All endpoints require authentication. Get a token first:
```bash
# Login to get token
curl -X POST "http://localhost:8080/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_username&password=your_password"

# Use token in subsequent requests
curl -X GET "http://localhost:8080/dashboard/overview" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📊 Dashboard Routes

### 1. Dashboard Overview
**GET** `/dashboard/overview`

Get complete dashboard overview with statistics from all ponds.

**Parameters:**
- `hours` (optional): Hours to look back for active ponds (default: 24)

**Response:**
```json
{
  "total_ponds": 2,
  "active_ponds": 1,
  "total_readings": 275,
  "total_anomalies": 5,
  "latest_readings": [
    {
      "pond_id": "pond_001",
      "device_id": "pond_001_sensor",
      "timestamp": "2025-07-18T23:34:36.542000",
      "ph": 7.2,
      "temperature": 25.5,
      "dissolved_oxygen": 6.8,
      "turbidity": 8.2,
      "nitrate": 12.3,
      "nitrite": 0.15,
      "ammonia": 0.08,
      "water_level": 1.8,
      "is_anomaly": false
    }
  ],
  "pond_stats": [
    {
      "pond_id": "pond_001",
      "total_readings": 250,
      "latest_reading": {...},
      "avg_ph": 7.15,
      "avg_temperature": 25.8,
      "avg_dissolved_oxygen": 6.9,
      "max_ph": 8.1,
      "min_ph": 6.8,
      "anomaly_count": 3,
      "last_update": "2025-07-18T23:34:36.542000"
    }
  ]
}
```

### 2. Latest Pond Data
**GET** `/dashboard/pond/{pond_id}/latest`

Get the most recent sensor data for a specific pond.

**Example:**
```bash
curl -X GET "http://localhost:8080/dashboard/pond/pond_001/latest" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Pond Statistics
**GET** `/dashboard/pond/{pond_id}/stats`

Get comprehensive statistics for a specific pond.

**Parameters:**
- `days` (optional): Number of days to analyze (default: 7)

**Response:**
```json
{
  "pond_id": "pond_001",
  "total_readings": 150,
  "latest_reading": {...},
  "avg_ph": 7.2,
  "avg_temperature": 25.8,
  "avg_dissolved_oxygen": 6.9,
  "max_ph": 8.1,
  "min_ph": 6.8,
  "max_temperature": 28.5,
  "min_temperature": 22.1,
  "max_dissolved_oxygen": 8.2,
  "min_dissolved_oxygen": 5.1,
  "anomaly_count": 3,
  "last_update": "2025-07-18T23:34:36.542000"
}
```

### 4. Sensor Trends
**GET** `/dashboard/pond/{pond_id}/trends`

Get sensor parameter trends for analysis.

**Parameters:**
- `hours` (optional): Hours to analyze for trends (default: 24)

**Response:**
```json
[
  {
    "pond_id": "pond_001",
    "parameter": "ph",
    "timestamps": ["2025-07-18T10:00:00", "2025-07-18T11:00:00"],
    "values": [7.2, 7.3, 7.1],
    "average": 7.2,
    "trend": "stable"
  }
]
```

### 5. Current Alerts
**GET** `/dashboard/alerts`

Get current alerts based on sensor readings.

**Parameters:**
- `hours` (optional): Hours to check for alerts (default: 24)
- `pond_id` (optional): Filter by specific pond
- `severity` (optional): Filter by severity (low, medium, high, critical)

**Response:**
```json
[
  {
    "pond_id": "pond_001",
    "alert_type": "ph_high",
    "parameter": "ph",
    "current_value": 8.7,
    "threshold_value": 8.5,
    "severity": "medium",
    "timestamp": "2025-07-18T23:30:00"
  }
]
```

### 6. Historical Data
**GET** `/dashboard/pond/{pond_id}/history`

Get historical sensor data with optional parameter filtering.

**Parameters:**
- `hours` (optional): Hours of history to retrieve (default: 24)
- `parameters` (optional): Comma-separated list of parameters

**Example:**
```bash
curl -X GET "http://localhost:8080/dashboard/pond/pond_001/history?hours=12&parameters=ph,temperature,dissolved_oxygen" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 7. Real-time Data
**GET** `/dashboard/realtime`

Get real-time data for all ponds (last 5 minutes).

**Response:**
```json
{
  "timestamp": "2025-07-18T23:35:00",
  "total_active_ponds": 2,
  "data": [
    {
      "pond_id": "pond_001",
      "device_id": "pond_001_sensor",
      "timestamp": "2025-07-18T23:34:36.542000",
      "ph": 7.2,
      "temperature": 25.5,
      "dissolved_oxygen": 6.8,
      "time_ago_seconds": 24
    }
  ]
}
```

---

## 🏊 Pond Management Integration Routes

### Base URL: `http://localhost:8080/ponds`

### 1. Management Overview
**GET** `/ponds/management/overview`

Get comprehensive pond management overview with sensor data integration.

**Parameters:**
- `farm_id` (optional): Filter by farm ID
- `status_filter` (optional): Filter by sensor status (active, inactive, warning, error)

**Response:**
```json
[
  {
    "id": "64f1a2b3c4d5e6f789012345",
    "name": "Main Pond",
    "farm_id": "64f1a2b3c4d5e6f789012340",
    "description": "Primary breeding pond",
    "size": 1000.5,
    "depth": 2.5,
    "fish_species": "Tilapia",
    "fish_count": 500,
    "created_at": "2025-01-15T10:00:00",
    "updated_at": "2025-01-15T10:00:00",
    "latest_reading": {
      "pond_id": "pond_001",
      "ph": 7.2,
      "temperature": 25.5
    },
    "sensor_status": "active",
    "last_data_time": "2025-07-18T23:34:36.542000",
    "total_readings_today": 144,
    "anomaly_count_today": 2,
    "avg_ph_today": 7.15,
    "avg_temperature_today": 25.8,
    "avg_dissolved_oxygen_today": 6.9
  }
]
```

### 2. Pond Management Details
**GET** `/ponds/{pond_id}/management/details`

Get detailed pond management information with sensor data.

**Response:** Same structure as above but for a single pond.

---

## 🚨 Alert System

The alert system automatically monitors sensor values and generates alerts based on these thresholds:

### pH Alerts
- **Normal**: 6.5 - 8.5
- **Medium Alert**: < 6.5 or > 8.5
- **Critical Alert**: < 6.0 or > 9.0

### Temperature Alerts (°C)
- **Normal**: 18.0 - 30.0
- **Medium Alert**: < 18.0 or > 30.0
- **Critical Alert**: < 15.0 or > 35.0

### Dissolved Oxygen Alerts (mg/L)
- **Normal**: 5.0 - 15.0
- **Medium Alert**: < 5.0 or > 15.0
- **Critical Alert**: < 3.0 or > 20.0

### Chemical Alerts (mg/L)
- **Ammonia**: Medium > 0.25, Critical > 0.5
- **Nitrite**: Medium > 0.2, Critical > 0.5
- **Nitrate**: Medium > 25.0, Critical > 40.0

---

## 📈 Dashboard Features

### Sensor Status Classification
- **Active**: Last reading within 15 minutes
- **Warning**: Last reading 15-60 minutes ago
- **Error**: Last reading over 60 minutes ago
- **Inactive**: No recent readings

### Trend Analysis
- **Increasing**: Recent average 5% higher than older average
- **Decreasing**: Recent average 5% lower than older average
- **Stable**: Change within 5%

---

## 🔄 Integration with MQTT Data

All dashboard endpoints automatically integrate with MQTT subscriber data:

1. **Real-time Updates**: Data is continuously updated via MQTT
2. **Anomaly Detection**: Built-in ML-based anomaly detection
3. **Historical Analysis**: Complete historical data access
4. **Multi-pond Support**: Supports multiple ponds simultaneously

---

## 💡 Usage Examples for Dashboard

### Get Dashboard Overview
```bash
curl -X GET "http://localhost:8080/dashboard/overview?hours=24" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Monitor Specific Pond
```bash
curl -X GET "http://localhost:8080/dashboard/pond/pond_001/stats?days=7" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Check Current Alerts
```bash
curl -X GET "http://localhost:8080/dashboard/alerts?severity=critical" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Real-time Data
```bash
curl -X GET "http://localhost:8080/dashboard/realtime" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Pond Management Overview
```bash
curl -X GET "http://localhost:8080/ponds/management/overview?status_filter=active" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔧 Technical Notes

- All timestamps are in UTC
- Sensor readings are automatically stored via MQTT
- Dashboard data is computed in real-time
- API supports filtering and pagination
- Authentication required for all endpoints
- CORS enabled for frontend integration

---

This comprehensive dashboard API provides everything needed for a complete pond monitoring and management system! 🌊📊
