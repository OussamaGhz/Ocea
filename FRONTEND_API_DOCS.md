# 🌊 Pond Monitoring MVP API Documentation

## Overview

This document provides complete API documentation for the Pond Monitoring System MVP. The API provides real-time sensor data, alert management, and dashboard functionality for aquaculture monitoring.

**Base URL**: `http://localhost:8000`  
**WebSocket URL**: `ws://localhost:8000/mvp/ws`

## Authentication

Most endpoints require Bearer token authentication. Obtain a token using the login endpoint.

### Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=secret
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Use the token in subsequent requests:**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 📊 MVP Dashboard Routes

### 1. Dashboard Overview
Get comprehensive system overview with statistics and pond status.

```http
GET /mvp/dashboard/overview
Authorization: Bearer {token}
```

**Response:**
```json
{
  "summary": {
    "total_ponds": 3,
    "active_ponds": 3,
    "total_readings": 1011,
    "active_alerts": 3,
    "critical_alerts": 1
  },
  "ponds": [
    {
      "pond_id": "pond_001",
      "status": "active",
      "latest_reading": {
        "timestamp": "2025-07-19T00:08:52.528000",
        "ph": 7.36,
        "temperature": 25.51,
        "dissolved_oxygen": 7.62,
        "water_level": 1.57
      }
    }
  ],
  "alert_statistics": {
    "total_alerts": 5,
    "by_severity": {
      "low": 0,
      "medium": 2,
      "high": 2,
      "critical": 1
    },
    "by_parameter": {
      "ammonia": 1,
      "dissolved_oxygen": 1,
      "temperature": 1,
      "turbidity": 1,
      "ph": 1
    },
    "active_alerts": 3,
    "period_days": 7
  },
  "websocket_connections": 0
}
```

### 2. Latest Pond Data
Get the most recent sensor reading for a specific pond.

```http
GET /mvp/pond/{pond_id}/latest
Authorization: Bearer {token}
```

**Example:**
```http
GET /mvp/pond/pond_001/latest
```

**Response:**
```json
{
  "pond_id": "pond_001",
  "latest_reading": {
    "pond_id": "pond_001",
    "device_id": "sensor_001",
    "timestamp": "2025-07-19T00:08:52.528000",
    "ph": 7.36,
    "temperature": 25.51,
    "dissolved_oxygen": 7.62,
    "turbidity": 2.86,
    "nitrate": 15.66,
    "nitrite": 0.256,
    "ammonia": 0.119,
    "water_level": 1.57,
    "created_at": "2025-07-19T00:08:52.540000",
    "id": "687ae21445b6fc5b6e454782"
  },
  "active_alerts": 2,
  "status": "active",
  "last_updated": "2025-07-19T00:08:52.528000"
}
```

### 3. Historical Pond Data
Get historical sensor readings for a specific pond.

```http
GET /mvp/pond/{pond_id}/history?hours={hours}
Authorization: Bearer {token}
```

**Parameters:**
- `hours` (optional): Number of hours of history to fetch (default: 24)

**Example:**
```http
GET /mvp/pond/pond_001/history?hours=6
```

**Response:**
```json
{
  "pond_id": "pond_001",
  "period_hours": 6,
  "total_readings": 12,
  "readings": [
    {
      "pond_id": "pond_001",
      "device_id": "sensor_001",
      "timestamp": "2025-07-18T18:38:52.528000",
      "ph": 6.94,
      "temperature": 25.21,
      "dissolved_oxygen": 7.19,
      "turbidity": 2.95,
      "nitrate": 19.62,
      "nitrite": 0.158,
      "ammonia": 0.113,
      "water_level": 1.66,
      "created_at": "2025-07-19T00:08:52.539000",
      "id": "687ae21445b6fc5b6e454761"
    }
  ]
}
```

### 4. Pond Alerts
Get alerts for a specific pond.

```http
GET /mvp/pond/{pond_id}/alerts?active_only={boolean}&limit={number}
Authorization: Bearer {token}
```

**Parameters:**
- `active_only` (optional): Show only unresolved alerts (default: true)
- `limit` (optional): Maximum number of alerts (default: 50)

**Example:**
```http
GET /mvp/pond/pond_001/alerts?active_only=true&limit=10
```

**Response:**
```json
{
  "pond_id": "pond_001",
  "alerts": [
    {
      "id": "687ae21445b6fc5b6e454788",
      "pond_id": "pond_001",
      "alert_type": "ammonia_high",
      "parameter": "ammonia",
      "current_value": 0.7,
      "threshold_value": 0.5,
      "severity": "critical",
      "message": "CRITICAL: Ammonia above threshold: 0.7 (limit: 0.5)",
      "is_resolved": false,
      "sms_sent": true,
      "created_at": "2025-07-18T23:38:52.558000"
    }
  ],
  "statistics": {
    "total_alerts": 5,
    "by_severity": {
      "low": 0,
      "medium": 2,
      "high": 2,
      "critical": 1
    },
    "active_alerts": 3,
    "period_days": 7
  },
  "total_returned": 2
}
```

### 5. Active Alerts (All Ponds)
Get all active alerts across all ponds.

```http
GET /mvp/alerts/active
Authorization: Bearer {token}
```

**Response:**
```json
{
  "total_active_alerts": 3,
  "alerts": [
    {
      "id": "687ae21445b6fc5b6e454788",
      "pond_id": "pond_001",
      "alert_type": "ammonia_high",
      "parameter": "ammonia",
      "current_value": 0.7,
      "threshold_value": 0.5,
      "severity": "critical",
      "message": "CRITICAL: Ammonia above threshold: 0.7 (limit: 0.5)",
      "is_resolved": false,
      "sms_sent": true,
      "created_at": "2025-07-18T23:38:52.558000"
    }
  ],
  "by_severity": {
    "critical": 1,
    "high": 2,
    "medium": 0,
    "low": 0
  }
}
```

### 6. Resolve Alert
Mark an alert as resolved.

```http
POST /mvp/alert/{alert_id}/resolve
Authorization: Bearer {token}
```

**Example:**
```http
POST /mvp/alert/687ae21445b6fc5b6e454788/resolve
```

**Response:**
```json
{
  "message": "Alert resolved successfully",
  "alert_id": "687ae21445b6fc5b6e454788"
}
```

### 7. System Status
Get system health and service status.

```http
GET /mvp/system/status
Authorization: Bearer {token}
```

**Response:**
```json
{
  "system_status": "operational",
  "database": "connected",
  "sms_service": "disabled",
  "websocket_connections": 0,
  "last_data_received": "2025-07-19T00:08:52.528000",
  "timestamp": "2025-07-19T00:53:12.123000"
}
```

---

## 🔌 WebSocket Real-time Data

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/mvp/ws');
```

### Message Types

#### 1. Sensor Data
Real-time sensor readings from ponds.

```json
{
  "type": "sensor_data",
  "data": {
    "pond_id": "pond_001",
    "device_id": "sensor_001",
    "timestamp": "2025-07-19T00:52:37.712000",
    "ph": 7.2,
    "temperature": 25.53,
    "dissolved_oxygen": 6.8,
    "turbidity": 8.13,
    "nitrate": 12.42,
    "nitrite": 0.151,
    "ammonia": 0.081,
    "water_level": 1.81
  },
  "timestamp": "2025-07-19T00:52:37.798000"
}
```

#### 2. Alerts
Real-time alert notifications.

```json
{
  "type": "alert",
  "data": {
    "id": "687ae45299fcbd1f799a5889",
    "pond_id": "pond_001",
    "parameter": "temperature",
    "current_value": 32.5,
    "threshold_value": 30.0,
    "severity": "high",
    "message": "HIGH: Temperature above threshold: 32.5 (limit: 30.0)",
    "sms_sent": true,
    "created_at": "2025-07-19T00:52:45.123000"
  },
  "timestamp": "2025-07-19T00:52:45.200000"
}
```

#### 3. Connection Status
Keep-alive messages.

```json
{
  "type": "pong",
  "message": "Connection active"
}
```

---

## 🔧 System Routes

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-18T10:30:00Z",
  "services": {
    "api": "running",
    "database": "connected",
    "mqtt_client": "connected",
    "websocket_connections": 0
  }
}
```

### Service Status
```http
GET /services/status
```

**Response:**
```json
{
  "api": {
    "status": "running",
    "version": "1.0.0"
  },
  "database": {
    "status": "connected"
  },
  "mqtt_client": {
    "status": "connected",
    "broker": "broker.hivemq.com:1883"
  },
  "websocket": {
    "active_connections": 0
  },
  "sms_service": {
    "status": "disabled"
  }
}
```

### Test SMS (Admin Only)
```http
POST /mvp/test/sms
Authorization: Bearer {admin_token}
```

**Response:**
```json
{
  "status": "success",
  "message": "Test SMS sent successfully"
}
```

---

## 📊 Data Models

### Sensor Reading
```json
{
  "pond_id": "string",
  "device_id": "string",
  "timestamp": "datetime",
  "ph": "number (6.0-9.0)",
  "temperature": "number (°C)",
  "dissolved_oxygen": "number (mg/L)",
  "turbidity": "number (NTU)",
  "nitrate": "number (mg/L)",
  "nitrite": "number (mg/L)",
  "ammonia": "number (mg/L)",
  "water_level": "number (meters)",
  "created_at": "datetime",
  "id": "string"
}
```

### Alert
```json
{
  "id": "string",
  "pond_id": "string",
  "alert_type": "string",
  "parameter": "string",
  "current_value": "number",
  "threshold_value": "number",
  "severity": "critical|high|medium|low",
  "message": "string",
  "is_resolved": "boolean",
  "sms_sent": "boolean",
  "created_at": "datetime",
  "resolved_at": "datetime|null"
}
```

---

## 🎯 Frontend Implementation Examples

### React WebSocket Hook
```javascript
import { useEffect, useState } from 'react';

function usePondWebSocket() {
  const [sensorData, setSensorData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/mvp/ws');
    
    ws.onopen = () => {
      setConnectionStatus('connected');
      console.log('🔌 WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'sensor_data') {
        setSensorData(message.data);
      } else if (message.type === 'alert') {
        setAlerts(prev => [message.data, ...prev]);
      }
    };
    
    ws.onclose = () => {
      setConnectionStatus('disconnected');
      console.log('📴 WebSocket disconnected');
    };

    return () => ws.close();
  }, []);

  return { sensorData, alerts, connectionStatus };
}
```

### Dashboard Data Fetching
```javascript
const API_BASE = 'http://localhost:8000';

class PondAPI {
  constructor(token) {
    this.token = token;
    this.headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  async getDashboardOverview() {
    const response = await fetch(`${API_BASE}/mvp/dashboard/overview`, {
      headers: this.headers
    });
    return response.json();
  }

  async getLatestPondData(pondId) {
    const response = await fetch(`${API_BASE}/mvp/pond/${pondId}/latest`, {
      headers: this.headers
    });
    return response.json();
  }

  async getPondHistory(pondId, hours = 24) {
    const response = await fetch(`${API_BASE}/mvp/pond/${pondId}/history?hours=${hours}`, {
      headers: this.headers
    });
    return response.json();
  }

  async getActiveAlerts() {
    const response = await fetch(`${API_BASE}/mvp/alerts/active`, {
      headers: this.headers
    });
    return response.json();
  }

  async resolveAlert(alertId) {
    const response = await fetch(`${API_BASE}/mvp/alert/${alertId}/resolve`, {
      method: 'POST',
      headers: this.headers
    });
    return response.json();
  }
}
```

### Dashboard Component Example
```javascript
function Dashboard({ token }) {
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const { sensorData, alerts } = usePondWebSocket();

  useEffect(() => {
    const api = new PondAPI(token);
    
    api.getDashboardOverview()
      .then(data => {
        setOverview(data);
        setLoading(false);
      })
      .catch(console.error);
  }, [token]);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="dashboard">
      <div className="summary-cards">
        <div className="card">
          <h3>Total Ponds</h3>
          <p>{overview.summary.total_ponds}</p>
        </div>
        <div className="card">
          <h3>Active Alerts</h3>
          <p>{overview.summary.active_alerts}</p>
        </div>
        <div className="card critical">
          <h3>Critical Alerts</h3>
          <p>{overview.summary.critical_alerts}</p>
        </div>
      </div>

      <div className="ponds-grid">
        {overview.ponds.map(pond => (
          <PondCard key={pond.pond_id} pond={pond} />
        ))}
      </div>

      <div className="real-time-alerts">
        <h3>Recent Alerts</h3>
        {alerts.map(alert => (
          <AlertItem key={alert.id} alert={alert} />
        ))}
      </div>
    </div>
  );
}
```

---

## 🚨 Error Handling

### Common HTTP Status Codes
- `200`: Success
- `401`: Unauthorized (missing or invalid token)
- `403`: Forbidden (insufficient permissions)
- `404`: Not found (pond/alert doesn't exist)
- `500`: Internal server error

### Error Response Format
```json
{
  "detail": "Error message",
  "error": true
}
```

---

## 📱 Sample Data Available

The system is pre-populated with:
- **3 Ponds**: pond_001, pond_002, pond_003
- **1,011 Sensor Readings**: 7 days of historical data
- **5 Alerts**: 3 active, 2 resolved
- **Test User**: admin/secret

---

## 🔗 Testing

### Test Credentials
```
Username: admin
Password: secret
```

### Quick Test Commands
```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret"

# Dashboard overview (replace TOKEN)
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/mvp/dashboard/overview

# Latest pond data
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/mvp/pond/pond_001/latest

# Active alerts
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/mvp/alerts/active
```

This API provides everything needed to build a comprehensive pond monitoring dashboard with real-time updates, historical data visualization, and alert management. 🌊📊
