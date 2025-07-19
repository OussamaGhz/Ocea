# Pond Simulators

This directory contains individual pond simulators that generate realistic sensor data for aquaculture monitoring.

## Overview

Each pond simulator is a separate Python script that:
- Generates realistic sensor data for 8 core parameters
- Publishes data to MQTT broker at regular intervals
- Can run independently on separate machines
- Simulates gradual sensor variations over time

## Core Sensor Parameters

Each pond simulator generates data for:

1. **pH** - Water acidity/alkalinity (6.5-8.5)
2. **Temperature** - Water temperature in Celsius (18-30°C)
3. **Dissolved Oxygen** - Oxygen content in mg/L (4-12 mg/L)
4. **Turbidity** - Water clarity in NTU (0.5-25 NTU)
5. **Nitrate** - Nitrate concentration in mg/L (0-40 mg/L)
6. **Nitrite** - Nitrite concentration in mg/L (0-0.5 mg/L)
7. **Ammonia** - Ammonia concentration in mg/L (0-0.5 mg/L)
8. **Water Level** - Water level in meters (0.8-2.5 m)

## Available Simulators

### Pond 001 Simulator (`pond_001_simulator.py`)
- **Pond ID**: pond_001
- **Device ID**: pond_001_sensor
- **Publish Interval**: 10 seconds
- **MQTT Topic**: sensors/pond_data

### Pond 002 Simulator (`pond_002_simulator.py`)
- **Pond ID**: pond_002
- **Device ID**: pond_002_sensor
- **Publish Interval**: 12 seconds
- **MQTT Topic**: sensors/pond_data

## Usage

### Running Individual Simulators

```bash
# Start pond 001 simulator
python simulators/pond_001_simulator.py

# Start pond 002 simulator
python simulators/pond_002_simulator.py
```

### Using the Launcher Script

```bash
# Start pond 001 simulator
python simulators/launch_simulators.py pond_001

# Start pond 002 simulator
python simulators/launch_simulators.py pond_002

# Get instructions for running both
python simulators/launch_simulators.py both
```

### Running Both Simulators

Open two separate terminal windows:

**Terminal 1:**
```bash
cd /home/oussama/ocea
python simulators/pond_001_simulator.py
```

**Terminal 2:**
```bash
cd /home/oussama/ocea
python simulators/pond_002_simulator.py
```

### Background Execution

To run simulators in the background:
```bash
python simulators/pond_001_simulator.py &
python simulators/pond_002_simulator.py &
```

## Configuration

Each simulator can be configured by modifying the `PondConfig` class in its respective file:

- `mqtt_broker`: MQTT broker hostname (default: broker.hivemq.com)
- `mqtt_port`: MQTT broker port (default: 1883)
- `publish_interval`: Seconds between sensor readings
- Sensor ranges for each parameter

## MQTT Message Format

Each simulator publishes JSON messages with this structure:

```json
{
  "pond_id": "pond_001",
  "device_id": "pond_001_sensor",
  "timestamp": "2025-07-18T18:30:00.000Z",
  "ph": 7.23,
  "temperature": 24.5,
  "dissolved_oxygen": 8.2,
  "turbidity": 12.4,
  "nitrate": 15.6,
  "nitrite": 0.12,
  "ammonia": 0.08,
  "water_level": 1.85
}
```

## Stopping Simulators

To stop a running simulator:
- Press `Ctrl+C` in the terminal where it's running
- For background processes, use: `pkill -f pond_001_simulator` or `pkill -f pond_002_simulator`

## Future Expansion

To add more ponds:
1. Copy an existing simulator file (e.g., `pond_001_simulator.py`)
2. Update the `PondConfig` class with new pond_id and device_id
3. Optionally adjust sensor ranges and publish intervals
4. Add the new simulator to the launcher script

## Dependencies

- `paho-mqtt`: MQTT client library
- `python-dateutil`: Date/time handling
- Standard Python libraries (json, time, random, logging)

## Troubleshooting

### Connection Issues
- Ensure internet connectivity for MQTT broker access
- Check broker hostname and port settings
- Verify firewall settings allow MQTT traffic

### Data Not Appearing
- Confirm MQTT subscriber is running
- Check topic names match between simulator and subscriber
- Verify database connection and storage

### Performance
- Adjust publish intervals if needed
- Monitor system resources when running multiple simulators
- Consider using local MQTT broker for high-volume testing
