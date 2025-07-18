# Pond Monitoring Backend

A FastAPI-based backend service for IoT pond monitoring system with MQTT data ingestion, ML-based anomaly detection, and comprehensive CRUD operations.

## Features

- **MQTT Data Ingestion**: Real-time data collection from IoT sensors via MQTT
- **MongoDB Integration**: Efficient data storage with ODM using Motor
- **Authentication & Authorization**: JWT-based secure authentication
- **Anomaly Detection**: Random Forest ML model for detecting anomalies in sensor data
- **CRUD Operations**: Complete REST API for all entities
- **Real-time Monitoring**: WebSocket support for live data streaming
- **Node-RED Compatible**: Designed to work with Node-RED MQTT implementations

## Quick Start

1. **Clone and Setup**
   ```bash
   git clone <repository>
   cd ocea
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start MongoDB**
   ```bash
   # Using Docker
   docker run -d -p 27017:27017 --name mongodb mongo:latest
   
   # Or install MongoDB locally
   ```

4. **Run the Application**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Start MQTT Subscriber**
   ```bash
   python -m app.mqtt.subscriber
   ```

## API Documentation

Once running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Architecture

```
app/
├── main.py              # FastAPI application entry point
├── config/              # Configuration management
├── auth/                # Authentication & authorization
├── models/              # Database models (ODM)
├── schemas/             # Pydantic schemas
├── api/                 # API routes
├── services/            # Business logic
├── mqtt/                # MQTT client and handlers
├── ml/                  # Machine learning models
└── database/            # Database connection and utilities
```

## MQTT Topics

The system subscribes to: `farm1/+/data`

Expected message format:
```json
{
  "pond_id": "pond_001",
  "timestamp": "2025-01-18T10:30:00Z",
  "temperature": 25.5,
  "ph": 7.2,
  "dissolved_oxygen": 8.5,
  "turbidity": 12.3
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| MONGODB_URL | MongoDB connection string | mongodb://localhost:27017 |
| SECRET_KEY | JWT secret key | - |
| MQTT_BROKER_HOST | MQTT broker hostname | localhost |
| MQTT_BROKER_PORT | MQTT broker port | 1883 |

## Development

- **Code Style**: Follow PEP 8
- **Testing**: Run `pytest` for unit tests
- **Linting**: Use `flake8` and `black` for code formatting
