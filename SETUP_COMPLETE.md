# 🐟 Pond Monitoring Backend - Setup Complete!

## Project Structure

```
ocea/
├── app/                        # Main application package
│   ├── __init__.py
│   ├── main.py                # FastAPI application entry point
│   ├── config.py              # Configuration management
│   ├── auth/                  # Authentication & authorization
│   │   ├── __init__.py
│   │   └── auth.py           # JWT authentication logic
│   ├── database/              # Database connection & utilities
│   │   ├── __init__.py
│   │   └── connection.py     # MongoDB connection
│   ├── models/                # Database models (ODM)
│   │   ├── __init__.py
│   │   └── models.py         # Pydantic models for MongoDB
│   ├── schemas/               # Pydantic schemas for API
│   │   ├── __init__.py
│   │   └── schemas.py        # Request/response schemas
│   ├── services/              # Business logic layer
│   │   ├── __init__.py
│   │   └── database_service.py # CRUD operations
│   ├── api/                   # API route handlers
│   │   ├── __init__.py
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── users.py          # User management
│   │   ├── farms.py          # Farm management
│   │   ├── ponds.py          # Pond management
│   │   ├── sensor_readings.py # Sensor data endpoints
│   │   ├── alerts.py         # Alert management
│   │   └── ml.py             # ML model endpoints
│   ├── mqtt/                  # MQTT client and handlers
│   │   ├── __init__.py
│   │   ├── client.py         # MQTT client implementation
│   │   └── subscriber.py     # MQTT subscriber service
│   └── ml/                    # Machine learning models
│       ├── __init__.py
│       └── anomaly_detection.py # Random Forest anomaly detection
├── scripts/                   # Utility scripts
│   ├── setup.py              # Database setup and admin user creation
│   ├── mqtt_test_publisher.py # MQTT test data generator
│   └── migrate.py            # Database migration script
├── docker/                    # Docker configuration files
│   ├── mongo-init.js         # MongoDB initialization
│   └── mosquitto.conf        # MQTT broker configuration
├── docs/                      # Documentation
│   ├── API.md                # API documentation
│   └── MQTT.md               # MQTT integration guide
├── models/                    # ML model storage (created at runtime)
├── requirements.txt           # Python dependencies
├── .env                      # Environment configuration (configured)
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
├── Dockerfile                # Docker container definition
├── docker-compose.yml        # Multi-container setup
├── package.json              # Project metadata
├── start.sh                  # Startup script (executable)
└── README.md                 # Project documentation
```

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   cd /home/oussama/ocea
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Start MongoDB** (if not using Docker)
   ```bash
   # Install MongoDB or use Docker
   docker run -d -p 27017:27017 --name mongodb mongo:latest
   ```

3. **Start MQTT Broker** (if not using Docker)
   ```bash
   # Install Mosquitto or use Docker
   docker run -d -p 1883:1883 --name mosquitto eclipse-mosquitto:2.0
   ```

4. **Setup Database and Admin User**
   ```bash
   python scripts/setup.py
   ```

5. **Start the Application**
   ```bash
   ./start.sh
   ```
   
   Or start services individually:
   ```bash
   ./start.sh api      # Start only API server
   ./start.sh mqtt     # Start only MQTT subscriber
   ```

6. **Access the API**
   - **API Documentation**: http://localhost:8000/docs
   - **Health Check**: http://localhost:8000/health

## 🐳 Docker Deployment

```bash
# Start all services with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🧪 Testing

1. **Test MQTT Publisher**
   ```bash
   python scripts/mqtt_test_publisher.py --duration 5
   ```

2. **Manual API Testing**
   ```bash
   # Register user
   curl -X POST "http://localhost:8000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","email":"test@example.com","password":"password123"}'
   
   # Login
   curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=testuser&password=password123"
   ```

## 🔧 Configuration

Edit `.env` file to configure:
- MongoDB connection
- MQTT broker settings
- JWT secret key
- API server settings

## 📊 Features Implemented

✅ **Core Backend Operations**
- User authentication (JWT)
- CRUD operations for Users, Farms, Ponds
- Sensor reading storage and retrieval
- Alert management

✅ **MQTT Data Ingestion**
- MQTT subscriber for sensor data
- Real-time data processing
- Compatible with Node-RED and ESP32

✅ **Machine Learning**
- Random Forest anomaly detection
- Rule-based anomaly detection
- Model training and persistence
- Feature importance analysis

✅ **Database Integration**
- MongoDB with Motor (async ODM)
- Indexed collections for performance
- Data validation with Pydantic

✅ **API Documentation**
- Interactive Swagger UI
- Comprehensive endpoint documentation
- Request/response schemas

## 🌐 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login

### Users
- `GET /users/` - List users (admin)
- `GET /users/me` - Current user info
- `PUT /users/{id}` - Update user (admin)

### Farms
- `POST /farms/` - Create farm
- `GET /farms/` - List user's farms
- `GET /farms/{id}` - Get farm details

### Ponds
- `POST /ponds/` - Create pond
- `GET /ponds/farm/{farm_id}` - List farm's ponds
- `GET /ponds/{id}` - Get pond details

### Sensor Readings
- `POST /sensor-readings/` - Manual reading entry
- `GET /sensor-readings/pond/{pond_id}` - Get pond readings
- `GET /sensor-readings/pond/{pond_id}/latest` - Latest reading

### Alerts
- `GET /alerts/pond/{pond_id}` - Get pond alerts
- `PUT /alerts/{id}/acknowledge` - Acknowledge alert

### Machine Learning
- `POST /ml/train` - Train anomaly model (admin)
- `GET /ml/model-info` - Model information (admin)
- `GET /ml/stats` - ML statistics (admin)

## 🔍 MQTT Message Format

ESP32/Node-RED should publish to `farm1/{pond_id}/data`:

```json
{
  "pond_id": "pond_001",
  "timestamp": "2025-01-18T10:30:00Z",
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

## 🤖 Anomaly Detection

The system uses:
1. **Random Forest Classifier** - Supervised learning from historical data
2. **Isolation Forest** - Unsupervised outlier detection
3. **Rule-based Detection** - Parameter range validation

Normal ranges for water quality parameters are built-in and configurable.

## 📝 Next Steps

1. **Frontend Development** - Create React/Vue.js dashboard
2. **Real-time WebSocket** - Live data streaming
3. **Push Notifications** - Mobile/email alerts
4. **Advanced ML** - Time series forecasting
5. **Data Visualization** - Charts and graphs
6. **Mobile App** - React Native/Flutter app

## 🆘 Troubleshooting

Check logs:
```bash
# API logs
docker logs pond_api

# MQTT subscriber logs  
docker logs pond_mqtt_subscriber

# MongoDB logs
docker logs pond_mongodb
```

Common issues:
- MongoDB connection failed → Check connection string in `.env`
- MQTT not receiving → Verify broker settings and topic format
- API authentication failed → Check JWT secret key configuration

## 🎯 Production Deployment

1. **Security**
   - Change default secret keys
   - Enable MQTT authentication
   - Use HTTPS/TLS
   - Configure CORS properly

2. **Performance**
   - Add Redis for caching
   - Configure MongoDB replica set
   - Use load balancer for API

3. **Monitoring**
   - Add logging aggregation
   - Set up health checks
   - Configure alerting

---

**🎉 Your pond monitoring backend is ready!** 

Start with `./start.sh` and visit http://localhost:8000/docs to explore the API.
