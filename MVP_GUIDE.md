# 🌊 Pond Monitoring System MVP

## 🎯 MVP Features Implemented

Your pond monitoring system MVP is now complete with the following features:

### ✅ **Real-time Data Collection**
- **MQTT Integration**: Receives sensor data from pond simulators
- **WebSocket Support**: Real-time data streaming to frontend
- **Automatic Storage**: Sensor readings stored in MongoDB
- **Multi-pond Support**: Ready for multiple pond monitoring

### ✅ **Smart Alert System**
- **Threshold Monitoring**: Automatic detection of sensor value violations
- **Severity Levels**: Critical, High, Medium, Low alerts
- **SMS Notifications**: Twilio integration for critical alerts
- **Alert Management**: Create, view, and resolve alerts

### ✅ **MVP Dashboard API**
- **Real-time Endpoints**: Live data for frontend integration
- **Historical Data**: Trend analysis and historical readings
- **Alert Dashboard**: Comprehensive alert management
- **System Status**: Health checks and service monitoring

## 🚀 Quick Start

### 1. **Server Status**
✅ **FastAPI Server**: Running on `http://localhost:8000`  
✅ **MQTT Client**: Connected to `broker.hivemq.com`  
✅ **Database**: MongoDB connected to `pond_monitoring`  
✅ **WebSocket**: Available at `ws://localhost:8000/mvp/ws`  

### 2. **Key API Endpoints**

#### **MVP Dashboard** (`/mvp/`)
```bash
# Real-time WebSocket connection
ws://localhost:8000/mvp/ws

# Latest pond data
GET /mvp/pond/pond_001/latest

# Pond historical data (last 24 hours)
GET /mvp/pond/pond_001/history?hours=24

# Active alerts
GET /mvp/alerts/active

# Pond alerts
GET /mvp/pond/pond_001/alerts

# Dashboard overview
GET /mvp/dashboard/overview

# System status
GET /mvp/system/status
```

#### **Traditional API** (backward compatible)
```bash
# Health check
GET /health

# Service status
GET /services/status

# Authentication
POST /auth/login
```

### 3. **WebSocket Integration**

Connect to `ws://localhost:8000/mvp/ws` to receive:

```javascript
// Real-time sensor data
{
  "type": "sensor_data",
  "data": {
    "pond_id": "pond_001",
    "ph": 7.2,
    "temperature": 25.5,
    "dissolved_oxygen": 8.3,
    "timestamp": "2025-07-19T00:50:23"
  }
}

// Real-time alerts
{
  "type": "alert",
  "data": {
    "pond_id": "pond_001",
    "parameter": "temperature",
    "current_value": 32.5,
    "threshold_value": 30.0,
    "severity": "high",
    "message": "HIGH: Temperature above threshold: 32.5 (limit: 30.0)"
  }
}
```

## 📱 SMS Alerts Configuration

### **Twilio Setup**
1. Create a Twilio account at https://www.twilio.com
2. Get your Account SID and Auth Token
3. Purchase a Twilio phone number
4. Update `.env` file with credentials:

```bash
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
ALERT_PHONE_NUMBER=+1987654321
```

### **Test SMS Service**
```bash
POST /mvp/test/sms
Authorization: Bearer your_admin_token
```

## ⚙️ Sensor Thresholds

Current thresholds (configurable in `.env`):

| Parameter | Min | Max | Critical Min | Critical Max |
|-----------|-----|-----|--------------|--------------|
| pH | 6.5 | 8.5 | 6.0 | 9.0 |
| Temperature (°C) | 20.0 | 30.0 | 15.0 | 35.0 |
| Dissolved Oxygen (mg/L) | 5.0 | 15.0 | 3.0 | 20.0 |
| Turbidity (NTU) | - | 10.0 | - | 20.0 |
| Nitrate (mg/L) | - | 40.0 | - | 80.0 |
| Nitrite (mg/L) | - | 0.5 | - | 1.0 |
| Ammonia (mg/L) | - | 0.5 | - | 1.0 |
| Water Level (m) | 0.5 | 3.0 | 0.2 | 4.0 |

## 🛠️ Frontend Integration Examples

### **React WebSocket Hook**
```javascript
import { useEffect, useState } from 'react';

function usePondWebSocket() {
  const [data, setData] = useState(null);
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/mvp/ws');
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'sensor_data') {
        setData(message.data);
      } else if (message.type === 'alert') {
        setAlerts(prev => [message.data, ...prev]);
      }
    };

    return () => ws.close();
  }, []);

  return { data, alerts };
}
```

### **Dashboard Data Fetching**
```javascript
// Get latest pond data
const response = await fetch('/mvp/pond/pond_001/latest');
const pondData = await response.json();

// Get active alerts
const alertsResponse = await fetch('/mvp/alerts/active');
const alerts = await alertsResponse.json();

// Get dashboard overview
const overviewResponse = await fetch('/mvp/dashboard/overview');
const overview = await overviewResponse.json();
```

## 📊 Database Structure

### **Sensor Readings Collection**
```javascript
{
  "_id": ObjectId,
  "pond_id": "pond_001",
  "device_id": "esp32_001",
  "timestamp": ISODate,
  "ph": 7.2,
  "temperature": 25.5,
  "dissolved_oxygen": 8.3,
  "turbidity": 2.1,
  "nitrate": 15.0,
  "nitrite": 0.2,
  "ammonia": 0.1,
  "water_level": 1.5,
  "created_at": ISODate
}
```

### **Alerts Collection**
```javascript
{
  "_id": ObjectId,
  "pond_id": "pond_001",
  "sensor_reading_id": ObjectId,
  "alert_type": "temperature_high",
  "parameter": "temperature",
  "current_value": 32.5,
  "threshold_value": 30.0,
  "severity": "high",
  "message": "Temperature above threshold",
  "is_resolved": false,
  "sms_sent": true,
  "created_at": ISODate
}
```

## 🔧 Troubleshooting

### **Common Issues**

1. **MQTT Not Connecting**
   ```bash
   # Check MQTT broker status
   GET /services/status
   ```

2. **SMS Not Working**
   ```bash
   # Test SMS configuration
   POST /mvp/test/sms
   ```

3. **WebSocket Disconnections**
   ```bash
   # Check WebSocket connections
   GET /mvp/system/status
   ```

### **Logs Location**
- Application logs: Console output
- MQTT logs: Console output with detailed connection info

## 🎉 Next Steps

1. **Frontend Development**: Use the WebSocket and REST APIs to build your dashboard
2. **Mobile App**: Connect to the same APIs for mobile monitoring
3. **Additional Sensors**: Add more ponds by updating pond_id in your simulators
4. **Custom Thresholds**: Modify threshold values in `.env` for your specific requirements
5. **Production Deployment**: Configure proper security, SSL, and production database

Your MVP is ready for frontend integration! 🚀
