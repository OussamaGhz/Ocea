#!/bin/bash

# Pond Monitoring System Demo Script
echo "🐟 Pond Monitoring System Demo"
echo "================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}✓ FastAPI Server: Running on http://localhost:8000${NC}"
echo -e "${BLUE}✓ MongoDB: Running in Docker${NC}"
echo -e "${BLUE}✓ MQTT Broker: Running in Docker${NC}"

echo ""
echo -e "${YELLOW}📊 System Status:${NC}"
curl -s http://localhost:8000/ | jq

echo ""
echo -e "${YELLOW}🏡 Available Farms:${NC}"
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc1MjgwMjk1MX0.AoXxQ-pg_obBOv4N3A_j1-X7AYoNjw5EcZ34QflRqxM"
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/farms/ | jq

echo ""
echo -e "${YELLOW}🐟 Ponds in Demo Farm:${NC}"
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/ponds/ | jq

echo ""
echo -e "${GREEN}🌊 Publishing sample sensor data via MQTT...${NC}"

# Publish multiple sensor readings
docker exec pond_mosquitto mosquitto_pub -h localhost -t "farm1/pond1/data" -m '{
  "pond_id": "6879a135ffcfb133e6bae245",
  "sensor_type": "temperature",
  "value": 26.5,
  "unit": "celsius",
  "timestamp": "2025-07-18T01:25:00Z",
  "device_id": "esp32_001"
}'

docker exec pond_mosquitto mosquitto_pub -h localhost -t "farm1/pond1/data" -m '{
  "pond_id": "6879a135ffcfb133e6bae245",
  "sensor_type": "ph",
  "value": 7.8,
  "unit": "pH",
  "timestamp": "2025-07-18T01:25:01Z",
  "device_id": "esp32_001"
}'

docker exec pond_mosquitto mosquitto_pub -h localhost -t "farm1/pond1/data" -m '{
  "pond_id": "6879a135ffcfb133e6bae245",
  "sensor_type": "dissolved_oxygen",
  "value": 8.5,
  "unit": "mg/L",
  "timestamp": "2025-07-18T01:25:02Z",
  "device_id": "esp32_001"
}'

sleep 2

echo ""
echo -e "${GREEN}✅ Demo completed! Visit http://localhost:8000/docs to explore the API${NC}"
echo ""
echo -e "${BLUE}📚 Next steps:${NC}"
echo "1. Open API documentation: http://localhost:8000/docs"
echo "2. View real-time data as it arrives via MQTT"
echo "3. Check anomaly detection alerts"
echo "4. Connect your ESP32 devices to mqtt://localhost:1883"
echo ""
echo -e "${YELLOW}🔧 System Components:${NC}"
echo "• FastAPI Backend: Full CRUD operations, JWT authentication"
echo "• MongoDB: Document database for flexible data storage"
echo "• MQTT: Real-time sensor data ingestion from IoT devices"
echo "• ML Anomaly Detection: Rule-based detection (sklearn fallback ready)"
echo "• Node-RED Ready: Compatible with standard MQTT topics"
