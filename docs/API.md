# API Documentation

## Authentication

All API endpoints (except `/auth/register` and `/auth/login`) require authentication using JWT tokens.

### Register a new user
```http
POST /auth/register
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123"
}
```

### Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=testuser&password=password123
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Using the token
Include the token in the Authorization header:
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## Farms

### Create a farm
```http
POST /farms/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "My Fish Farm",
  "location": "Lake District, UK",
  "description": "Trout farming facility"
}
```

### Get user's farms
```http
GET /farms/
Authorization: Bearer <token>
```

### Get specific farm
```http
GET /farms/{farm_id}
Authorization: Bearer <token>
```

## Ponds

### Create a pond
```http
POST /ponds/
Authorization: Bearer <token>
Content-Type: application/json

{
  "pond_id": "pond_001",
  "name": "Pond Alpha",
  "farm_id": "64f8a1b2c3d4e5f6a7b8c9d0",
  "area": 1000.5,
  "depth": 2.5,
  "fish_species": "Rainbow Trout"
}
```

### Get ponds by farm
```http
GET /ponds/farm/{farm_id}
Authorization: Bearer <token>
```

## Sensor Readings

### Get readings for a pond
```http
GET /sensor-readings/pond/{pond_id}?start_date=2025-01-01T00:00:00Z&end_date=2025-01-31T23:59:59Z
Authorization: Bearer <token>
```

### Get latest reading for a pond
```http
GET /sensor-readings/pond/{pond_id}/latest
Authorization: Bearer <token>
```

### Manual sensor reading entry
```http
POST /sensor-readings/
Authorization: Bearer <token>
Content-Type: application/json

{
  "pond_id": "pond_001",
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

## Alerts

### Get alerts for a pond
```http
GET /alerts/pond/{pond_id}?acknowledged=false
Authorization: Bearer <token>
```

### Acknowledge an alert
```http
PUT /alerts/{alert_id}/acknowledge
Authorization: Bearer <token>
```

## Machine Learning

### Train anomaly detection model (Admin only)
```http
POST /ml/train
Authorization: Bearer <admin_token>
```

### Get model information (Admin only)
```http
GET /ml/model-info
Authorization: Bearer <admin_token>
```

### Get ML statistics (Admin only)
```http
GET /ml/stats
Authorization: Bearer <admin_token>
```

## WebSocket (Future Enhancement)

Real-time data streaming endpoint:
```
ws://localhost:8000/ws/pond/{pond_id}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "detail": "Error message",
  "error": true
}
```

Common HTTP status codes:
- `400` - Bad Request (validation error)
- `401` - Unauthorized (missing or invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Unprocessable Entity (validation error)
- `500` - Internal Server Error
