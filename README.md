# 🌊 Pond Monitoring System

A comprehensive FastAPI-based IoT aquaculture monitoring system with real-time data collection, intelligent alert management, and advanced analytics for pond farming operations.

## 🚀 Key Features

### 🔄 Real-time Data Collection
- **MQTT Integration**: Real-time sensor data ingestion from IoT devices
- **WebSocket Support**: Live data streaming for frontend applications
- **Multi-Pond Monitoring**: Support for multiple pond farms and locations
- **Automated Data Storage**: Efficient MongoDB storage with optimized schemas

### 🧠 Intelligent Analytics
- **ML-based Anomaly Detection**: Random Forest models for predictive monitoring
- **Chart Data API**: Structured endpoints for data visualization
- **Historical Analysis**: Trend analysis and statistical insights
- **Real-time Processing**: Instant data processing and alert generation

### 🚨 Smart Alert System
- **Threshold Monitoring**: Configurable sensor parameter thresholds
- **Multi-level Severity**: Critical, High, Medium, Low alert classifications
- **SMS Notifications**: Twilio integration for critical alert notifications
- **Alert Management**: Complete CRUD operations for alert handling

### 🌐 Comprehensive API
- **MVP Dashboard**: Ready-to-use endpoints for frontend integration
- **Authentication & Authorization**: JWT-based secure access control
- **RESTful Design**: Complete CRUD operations for all entities
- **Chart Data Endpoints**: Formatted data for popular charting libraries
- **WebSocket Real-time**: Live updates for dashboard applications

### 🔧 Developer Experience
- **Enhanced CORS**: Proper frontend integration support
- **MongoDB Serialization**: Custom utilities for seamless data handling
- **Comprehensive Documentation**: Detailed API docs and integration guides
- **Test Utilities**: Built-in testing tools and simulators

## 🏁 Quick Start

### Prerequisites
- Python 3.9+
- MongoDB (local or cloud)
- Git

### Installation

1. **Clone and Setup**

   ```bash
   git clone https://github.com/OussamaGhz/Ocea.git
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
   ```

4. **Run the Application**

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## 📚 API Documentation

Once running, access:

- **Interactive API Docs**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>

## 🏗 Architecture

```text
app/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management
├── auth/                # Authentication & authorization
├── models/              # Database models (ODM)
├── schemas/             # Pydantic schemas
├── api/                 # API routes
│   ├── mvp_dashboard.py # MVP dashboard with chart data
│   ├── dashboard.py     # Enhanced dashboard routes
│   ├── auth.py          # Authentication endpoints
│   ├── alerts.py        # Alert management
│   └── ...              # Other API modules
├── services/            # Business logic
│   ├── alert_service.py # Alert processing
│   ├── sms_service.py   # SMS notifications (Twilio)
│   └── database_service.py
├── utils/               # Utilities
│   └── mongo_serializer.py # MongoDB serialization
├── websocket/           # WebSocket management
│   └── manager.py       # Connection management
├── mqtt/                # MQTT client and handlers
│   ├── simple_client.py # Production MQTT client
│   └── subscriber.py    # Legacy subscriber
├── ml/                  # Machine learning models
│   └── anomaly_detection.py
└── database/            # Database connection and utilities
```

## 📡 MQTT Configuration

The system subscribes to: `sensors/+` (configurable)

Expected message format:

```json
{
  "pond_id": "pond_001",
  "timestamp": "2025-01-18T10:30:00Z",
  "temperature": 25.5,
  "ph": 7.2,
  "dissolved_oxygen": 8.5,
  "turbidity": 12.3,
  "nitrate": 15.2,
  "nitrite": 0.3,
  "ammonia": 0.1,
  "water_level": 1.8
}
```

## 🌐 API Endpoints

### MVP Dashboard API (`/mvp/`)
- **Dashboard Overview**: `GET /mvp/dashboard/overview` - System statistics and pond status
- **Latest Pond Data**: `GET /mvp/pond/{pond_id}/latest` - Most recent sensor readings
- **Historical Data**: `GET /mvp/pond/{pond_id}/history` - Historical sensor data with filtering
- **Chart Data**: `GET /mvp/pond/{pond_id}/chart-data` - Formatted data for charting libraries
- **Real-time Charts**: `GET /mvp/pond/{pond_id}/realtime-chart` - Live chart data
- **Pond Alerts**: `GET /mvp/pond/{pond_id}/alerts` - Pond-specific alerts
- **Active Alerts**: `GET /mvp/alerts/active` - All active system alerts
- **WebSocket**: `ws://localhost:8000/mvp/ws` - Real-time data streaming

### Enhanced Dashboard API (`/dashboard/`)
- **Complete Analytics**: Advanced dashboard with detailed statistics
- **Trend Analysis**: Sensor parameter trends and analytics
- **Alert Management**: Comprehensive alert system integration

### Authentication (`/auth/`)
- **Login**: `POST /auth/login` - JWT token authentication
- **User Management**: Complete user CRUD operations

### System Monitoring
- **Health Check**: `GET /health` - System health status
- **Service Status**: `GET /services/status` - Detailed service information

## 📊 Chart Data API

Specialized endpoints for frontend chart integration:

```javascript
// Get chart data for temperature over 24 hours
GET /mvp/pond/pond_001/chart-data?parameter=temperature&hours=24

// Real-time data for live charts (last 60 minutes)
GET /mvp/pond/pond_001/realtime-chart?parameter=temperature&minutes=60
```

Supports all sensor parameters: `temperature`, `ph`, `dissolved_oxygen`, `turbidity`, `nitrate`, `nitrite`, `ammonia`, `water_level`

## 🔌 WebSocket Integration

Real-time data streaming for live dashboards:

```javascript
const ws = new WebSocket('ws://localhost:8000/mvp/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'sensor_data') {
    // Update charts with real-time data
  } else if (data.type === 'alert') {
    // Handle new alerts
  }
};
```

## 🚨 Alert System

### Configurable Thresholds
- **pH**: 6.5 - 8.5 (optimal range)
- **Temperature**: 20°C - 30°C
- **Dissolved Oxygen**: 5.0 - 15.0 mg/L
- **Turbidity**: < 10 NTU
- **Nitrate**: < 40 mg/L
- **Nitrite**: < 0.5 mg/L
- **Ammonia**: < 0.5 mg/L
- **Water Level**: 0.5 - 3.0 m

### Alert Severity Levels
- **Critical**: Immediate action required, SMS notification sent
- **High**: Urgent attention needed
- **Medium**: Monitor closely
- **Low**: Informational

### SMS Notifications
Configure Twilio credentials in `.env` for critical alert notifications:

```bash
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_twilio_number
ALERT_PHONE_NUMBER=recipient_number
```

## ⚙️ Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| **Database** | | |
| MONGODB_URL | MongoDB connection string | mongodb://localhost:27017 |
| DATABASE_NAME | Database name | pond_monitoring |
| **Authentication** | | |
| SECRET_KEY | JWT secret key | your-secret-key-here |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token expiration time | 30 |
| **MQTT** | | |
| MQTT_BROKER_HOST | MQTT broker hostname | broker.hivemq.com |
| MQTT_BROKER_PORT | MQTT broker port | 1883 |
| MQTT_USERNAME | MQTT username (optional) | - |
| MQTT_PASSWORD | MQTT password (optional) | - |
| MQTT_TOPIC_PATTERN | MQTT topic pattern | sensors/+ |
| **SMS Alerts** | | |
| TWILIO_ACCOUNT_SID | Twilio account SID | - |
| TWILIO_AUTH_TOKEN | Twilio auth token | - |
| TWILIO_PHONE_NUMBER | Twilio phone number | - |
| ALERT_PHONE_NUMBER | Alert recipient number | - |
| **Sensor Thresholds** | | |
| PH_MIN / PH_MAX | pH thresholds | 6.5 / 8.5 |
| TEMPERATURE_MIN / TEMPERATURE_MAX | Temperature thresholds (°C) | 20.0 / 30.0 |
| DISSOLVED_OXYGEN_MIN / DISSOLVED_OXYGEN_MAX | DO thresholds (mg/L) | 5.0 / 15.0 |
| TURBIDITY_MAX | Maximum turbidity (NTU) | 10.0 |
| NITRATE_MAX | Maximum nitrate (mg/L) | 40.0 |
| NITRITE_MAX | Maximum nitrite (mg/L) | 0.5 |
| AMMONIA_MAX | Maximum ammonia (mg/L) | 0.5 |
| WATER_LEVEL_MIN / WATER_LEVEL_MAX | Water level thresholds (m) | 0.5 / 3.0 |

## 🛠 Development

### Code Quality
- **Style Guide**: PEP 8 compliance
- **Type Hints**: Full typing support with mypy
- **Formatting**: Black code formatter
- **Linting**: Flake8 for code quality

### Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Test MQTT connection
python mqtt_connection_test.py

# Test complete flow
python test_complete_flow.py
```

### Project Structure
```text
├── app/                 # Main application
├── docs/               # Documentation
├── esp32/              # ESP32 sensor code
├── examples/           # Example implementations
├── scripts/            # Utility scripts
├── simulators/         # Pond data simulators
├── requirements.txt    # Python dependencies
├── docker-compose.yml  # Docker configuration
└── README.md          # This file
```

## 📖 Documentation

- **[API Documentation](docs/API.md)** - Complete API reference
- **[MQTT Guide](docs/MQTT.md)** - MQTT setup and configuration
- **[Chart API Documentation](docs/CHART_API_DOCUMENTATION.md)** - Chart data integration
- **[Frontend API Guide](FRONTEND_API_DOCS.md)** - Frontend integration examples
- **[MVP Guide](MVP_GUIDE.md)** - MVP features and usage

## 🌐 Related Projects

### Frontend Applications
- **🎨 [Ocea Frontend Dashboard](https://github.com/arixstoo/Junction)** - React-based monitoring dashboard
- **🌐 [Ocea Showcase Website](https://github.com/arixstoo/Ocea-Website)** - Project showcase and landing page

### Getting Started with Frontend
1. Clone the frontend repository
2. Configure API endpoints to point to this backend (`http://localhost:8000`)
3. Use the authentication and chart data endpoints documented above
4. Connect to WebSocket for real-time updates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit a Pull Request

### Development Guidelines
- Follow PEP 8 style guide
- Add tests for new features
- Update documentation
- Ensure all tests pass before submitting PR

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** - Modern web framework for Python APIs
- **MongoDB** - Document-based database for sensor data
- **MQTT** - Lightweight messaging protocol for IoT
- **Twilio** - SMS notification service
- **Scikit-learn** - Machine learning capabilities

## 📞 Support

For support, feature requests, or bug reports:
1. Open an issue on GitHub
2. Check the documentation in the `docs/` folder
3. Review the example implementations in `examples/`

---

**Made with ❤️ by Amadeus**
