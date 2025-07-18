#!/bin/bash

# Pond Monitoring System - Start Script

echo "🐟 Starting Pond Monitoring System..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration before continuing"
    exit 1
fi

# Create models directory
mkdir -p models

# Function to start services
start_api() {
    echo "🚀 Starting API server with integrated MQTT subscriber..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    API_PID=$!
    echo "API server started with PID: $API_PID"
    echo "📡 MQTT subscriber will start automatically as a background service"
}

start_mqtt_only() {
    echo "📡 Starting MQTT subscriber only..."
    python -m app.mqtt.subscriber &
    MQTT_PID=$!
    echo "MQTT subscriber started with PID: $MQTT_PID"
}

# Trap to clean up background processes
cleanup() {
    echo "🛑 Stopping services..."
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null
    fi
    if [ ! -z "$MQTT_PID" ]; then
        kill $MQTT_PID 2>/dev/null
    fi
    echo "Services stopped"
    exit 0
}

trap cleanup INT TERM

# Parse command line arguments
case "$1" in
    "api")
        start_api
        wait $API_PID
        ;;
    "mqtt")
        start_mqtt_only
        wait $MQTT_PID
        ;;
    "setup")
        echo "🔧 Running setup..."
        python scripts/setup.py
        ;;
    "test")
        echo "🧪 Starting test MQTT publisher..."
        python scripts/mqtt_test_publisher.py
        ;;
    *)
        echo "Starting all services (API with integrated MQTT subscriber)..."
        start_api
        
        echo "✅ All services started!"
        echo "📊 API Documentation: http://localhost:8000/docs"
        echo "❤️  Health Check: http://localhost:8000/health"
        echo "🔧 Services Status: http://localhost:8000/services/status"
        echo ""
        echo "Press Ctrl+C to stop all services"
        
        # Wait for any background process to exit
        wait
        ;;
esac
