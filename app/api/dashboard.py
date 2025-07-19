from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.database.connection import get_database
from app.services.database_service import SensorReadingService, PondService, FarmService
from app.auth.auth import get_current_active_user
from app.models.models import User
from pydantic import BaseModel
from bson import ObjectId
import pymongo

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# Response Models
class LatestSensorData(BaseModel):
    pond_id: str
    device_id: Optional[str] = None
    timestamp: datetime
    ph: Optional[float] = None
    temperature: Optional[float] = None
    dissolved_oxygen: Optional[float] = None
    turbidity: Optional[float] = None
    nitrate: Optional[float] = None
    nitrite: Optional[float] = None
    ammonia: Optional[float] = None
    water_level: Optional[float] = None
    is_anomaly: bool = False

class PondStats(BaseModel):
    pond_id: str
    total_readings: int
    latest_reading: Optional[LatestSensorData] = None
    avg_ph: Optional[float] = None
    avg_temperature: Optional[float] = None
    avg_dissolved_oxygen: Optional[float] = None
    max_ph: Optional[float] = None
    min_ph: Optional[float] = None
    max_temperature: Optional[float] = None
    min_temperature: Optional[float] = None
    max_dissolved_oxygen: Optional[float] = None
    min_dissolved_oxygen: Optional[float] = None
    anomaly_count: int = 0
    last_update: Optional[datetime] = None

class DashboardOverview(BaseModel):
    total_ponds: int
    active_ponds: int  # ponds with recent data
    total_readings: int
    total_anomalies: int
    latest_readings: List[LatestSensorData]
    pond_stats: List[PondStats]

class SensorTrends(BaseModel):
    pond_id: str
    parameter: str
    timestamps: List[datetime]
    values: List[float]
    average: float
    trend: str  # "increasing", "decreasing", "stable"

class AlertSummary(BaseModel):
    pond_id: str
    alert_type: str
    parameter: str
    current_value: float
    threshold_value: float
    severity: str  # "low", "medium", "high", "critical"
    timestamp: datetime

# Helper Functions
def calculate_trend(values: List[float]) -> str:
    """Calculate trend based on recent values"""
    if len(values) < 2:
        return "stable"
    
    recent_avg = sum(values[-5:]) / min(len(values), 5)
    older_avg = sum(values[:5]) / min(len(values), 5)
    
    if recent_avg > older_avg * 1.05:
        return "increasing"
    elif recent_avg < older_avg * 0.95:
        return "decreasing"
    else:
        return "stable"

def check_sensor_alerts(reading: dict) -> List[AlertSummary]:
    """Check for sensor value alerts"""
    alerts = []
    
    # Define thresholds for alerts
    thresholds = {
        'ph': {'min': 6.5, 'max': 8.5, 'critical_min': 6.0, 'critical_max': 9.0},
        'temperature': {'min': 18.0, 'max': 30.0, 'critical_min': 15.0, 'critical_max': 35.0},
        'dissolved_oxygen': {'min': 5.0, 'max': 15.0, 'critical_min': 3.0, 'critical_max': 20.0},
        'ammonia': {'max': 0.25, 'critical_max': 0.5},
        'nitrite': {'max': 0.2, 'critical_max': 0.5},
        'nitrate': {'max': 25.0, 'critical_max': 40.0}
    }
    
    for param, limits in thresholds.items():
        value = reading.get(param)
        if value is None:
            continue
        
        severity = None
        threshold = None
        alert_type = None
        
        if 'critical_min' in limits and value < limits['critical_min']:
            severity = "critical"
            threshold = limits['critical_min']
            alert_type = f"{param}_critically_low"
        elif 'critical_max' in limits and value > limits['critical_max']:
            severity = "critical"
            threshold = limits['critical_max']
            alert_type = f"{param}_critically_high"
        elif 'min' in limits and value < limits['min']:
            severity = "medium"
            threshold = limits['min']
            alert_type = f"{param}_low"
        elif value > limits['max']:
            severity = "medium"
            threshold = limits['max']
            alert_type = f"{param}_high"
        
        if severity:
            alerts.append(AlertSummary(
                pond_id=reading['pond_id'],
                alert_type=alert_type,
                parameter=param,
                current_value=value,
                threshold_value=threshold,
                severity=severity,
                timestamp=reading.get('timestamp', datetime.utcnow())
            ))
    
    return alerts


@router.get("/overview", response_model=DashboardOverview)
async def get_dashboard_overview(
    hours: int = Query(24, description="Hours to look back for active ponds"),
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get complete dashboard overview"""
    
    # Get sensor readings collection
    sensor_readings = db.sensor_readings
    
    # Calculate time threshold for active ponds
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    
    # Get total statistics
    total_readings = sensor_readings.count_documents({})
    total_anomalies = sensor_readings.count_documents({"is_anomaly": True})
    
    # Get unique ponds
    pond_ids = sensor_readings.distinct("pond_id")
    total_ponds = len(pond_ids)
    
    # Get active ponds (with recent data)
    active_pond_ids = sensor_readings.distinct(
        "pond_id", 
        {"timestamp": {"$gte": time_threshold}}
    )
    active_ponds = len(active_pond_ids)
    
    # Get latest reading for each pond
    latest_readings = []
    pond_stats = []
    
    for pond_id in pond_ids:
        # Get latest reading for this pond
        latest = sensor_readings.find_one(
            {"pond_id": pond_id},
            sort=[("timestamp", -1)]
        )
        
        if latest:
            latest_reading = LatestSensorData(
                pond_id=latest['pond_id'],
                device_id=latest.get('device_id'),
                timestamp=latest['timestamp'],
                ph=latest.get('ph'),
                temperature=latest.get('temperature'),
                dissolved_oxygen=latest.get('dissolved_oxygen'),
                turbidity=latest.get('turbidity'),
                nitrate=latest.get('nitrate'),
                nitrite=latest.get('nitrite'),
                ammonia=latest.get('ammonia'),
                water_level=latest.get('water_level'),
                is_anomaly=latest.get('is_anomaly', False)
            )
            latest_readings.append(latest_reading)
            
            # Calculate statistics for this pond
            pond_readings = list(sensor_readings.find({"pond_id": pond_id}))
            
            if pond_readings:
                # Calculate averages and extremes
                ph_values = [r.get('ph') for r in pond_readings if r.get('ph') is not None]
                temp_values = [r.get('temperature') for r in pond_readings if r.get('temperature') is not None]
                do_values = [r.get('dissolved_oxygen') for r in pond_readings if r.get('dissolved_oxygen') is not None]
                
                stats = PondStats(
                    pond_id=pond_id,
                    total_readings=len(pond_readings),
                    latest_reading=latest_reading,
                    avg_ph=sum(ph_values) / len(ph_values) if ph_values else None,
                    avg_temperature=sum(temp_values) / len(temp_values) if temp_values else None,
                    avg_dissolved_oxygen=sum(do_values) / len(do_values) if do_values else None,
                    max_ph=max(ph_values) if ph_values else None,
                    min_ph=min(ph_values) if ph_values else None,
                    max_temperature=max(temp_values) if temp_values else None,
                    min_temperature=min(temp_values) if temp_values else None,
                    max_dissolved_oxygen=max(do_values) if do_values else None,
                    min_dissolved_oxygen=min(do_values) if do_values else None,
                    anomaly_count=len([r for r in pond_readings if r.get('is_anomaly')]),
                    last_update=latest['timestamp']
                )
                pond_stats.append(stats)
    
    return DashboardOverview(
        total_ponds=total_ponds,
        active_ponds=active_ponds,
        total_readings=total_readings,
        total_anomalies=total_anomalies,
        latest_readings=latest_readings,
        pond_stats=pond_stats
    )


@router.get("/pond/{pond_id}/latest", response_model=LatestSensorData)
async def get_pond_latest_data(
    pond_id: str,
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get latest sensor data for a specific pond"""
    
    sensor_readings = db.sensor_readings
    
    latest = sensor_readings.find_one(
        {"pond_id": pond_id},
        sort=[("timestamp", -1)]
    )
    
    if not latest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sensor data found for pond {pond_id}"
        )
    
    return LatestSensorData(
        pond_id=latest['pond_id'],
        device_id=latest.get('device_id'),
        timestamp=latest['timestamp'],
        ph=latest.get('ph'),
        temperature=latest.get('temperature'),
        dissolved_oxygen=latest.get('dissolved_oxygen'),
        turbidity=latest.get('turbidity'),
        nitrate=latest.get('nitrate'),
        nitrite=latest.get('nitrite'),
        ammonia=latest.get('ammonia'),
        water_level=latest.get('water_level'),
        is_anomaly=latest.get('is_anomaly', False)
    )


@router.get("/pond/{pond_id}/stats", response_model=PondStats)
async def get_pond_stats(
    pond_id: str,
    days: int = Query(7, description="Number of days to analyze"),
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get comprehensive statistics for a specific pond"""
    
    sensor_readings = db.sensor_readings
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    # Get readings for the time period
    readings = list(sensor_readings.find({
        "pond_id": pond_id,
        "timestamp": {"$gte": start_time, "$lte": end_time}
    }).sort("timestamp", -1))
    
    if not readings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sensor data found for pond {pond_id} in the last {days} days"
        )
    
    # Get latest reading
    latest = readings[0]
    latest_reading = LatestSensorData(
        pond_id=latest['pond_id'],
        device_id=latest.get('device_id'),
        timestamp=latest['timestamp'],
        ph=latest.get('ph'),
        temperature=latest.get('temperature'),
        dissolved_oxygen=latest.get('dissolved_oxygen'),
        turbidity=latest.get('turbidity'),
        nitrate=latest.get('nitrate'),
        nitrite=latest.get('nitrite'),
        ammonia=latest.get('ammonia'),
        water_level=latest.get('water_level'),
        is_anomaly=latest.get('is_anomaly', False)
    )
    
    # Calculate statistics
    ph_values = [r.get('ph') for r in readings if r.get('ph') is not None]
    temp_values = [r.get('temperature') for r in readings if r.get('temperature') is not None]
    do_values = [r.get('dissolved_oxygen') for r in readings if r.get('dissolved_oxygen') is not None]
    
    return PondStats(
        pond_id=pond_id,
        total_readings=len(readings),
        latest_reading=latest_reading,
        avg_ph=round(sum(ph_values) / len(ph_values), 2) if ph_values else None,
        avg_temperature=round(sum(temp_values) / len(temp_values), 2) if temp_values else None,
        avg_dissolved_oxygen=round(sum(do_values) / len(do_values), 2) if do_values else None,
        max_ph=round(max(ph_values), 2) if ph_values else None,
        min_ph=round(min(ph_values), 2) if ph_values else None,
        max_temperature=round(max(temp_values), 2) if temp_values else None,
        min_temperature=round(min(temp_values), 2) if temp_values else None,
        max_dissolved_oxygen=round(max(do_values), 2) if do_values else None,
        min_dissolved_oxygen=round(min(do_values), 2) if do_values else None,
        anomaly_count=len([r for r in readings if r.get('is_anomaly')]),
        last_update=latest['timestamp']
    )


@router.get("/pond/{pond_id}/trends", response_model=List[SensorTrends])
async def get_pond_trends(
    pond_id: str,
    hours: int = Query(24, description="Hours to analyze for trends"),
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get sensor trends for a specific pond"""
    
    sensor_readings = db.sensor_readings
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    # Get readings for the time period
    readings = list(sensor_readings.find({
        "pond_id": pond_id,
        "timestamp": {"$gte": start_time, "$lte": end_time}
    }).sort("timestamp", 1))  # Ascending order for trends
    
    if not readings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sensor data found for pond {pond_id} in the last {hours} hours"
        )
    
    trends = []
    parameters = ['ph', 'temperature', 'dissolved_oxygen', 'turbidity', 'nitrate', 'nitrite', 'ammonia', 'water_level']
    
    for param in parameters:
        values = []
        timestamps = []
        
        for reading in readings:
            if reading.get(param) is not None:
                values.append(reading[param])
                timestamps.append(reading['timestamp'])
        
        if values:
            trend = SensorTrends(
                pond_id=pond_id,
                parameter=param,
                timestamps=timestamps,
                values=values,
                average=round(sum(values) / len(values), 3),
                trend=calculate_trend(values)
            )
            trends.append(trend)
    
    return trends


@router.get("/alerts", response_model=List[AlertSummary])
async def get_current_alerts(
    hours: int = Query(24, description="Hours to check for alerts"),
    pond_id: Optional[str] = Query(None, description="Filter by specific pond"),
    severity: Optional[str] = Query(None, description="Filter by severity: low, medium, high, critical"),
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get current alerts based on latest sensor readings"""
    
    sensor_readings = db.sensor_readings
    
    # Build query
    query = {"timestamp": {"$gte": datetime.utcnow() - timedelta(hours=hours)}}
    if pond_id:
        query["pond_id"] = pond_id
    
    # Get latest reading for each pond in the time range
    pipeline = [
        {"$match": query},
        {"$sort": {"timestamp": -1}},
        {"$group": {
            "_id": "$pond_id",
            "latest": {"$first": "$$ROOT"}
        }}
    ]
    
    latest_readings = list(sensor_readings.aggregate(pipeline))
    
    all_alerts = []
    for result in latest_readings:
        reading = result['latest']
        alerts = check_sensor_alerts(reading)
        all_alerts.extend(alerts)
    
    # Filter by severity if specified
    if severity:
        all_alerts = [alert for alert in all_alerts if alert.severity == severity]
    
    return all_alerts


@router.get("/pond/{pond_id}/history")
async def get_pond_history(
    pond_id: str,
    hours: int = Query(24, description="Hours of history to retrieve"),
    parameters: Optional[str] = Query(None, description="Comma-separated list of parameters to include"),
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get historical sensor data for a pond with optional parameter filtering"""
    
    sensor_readings = db.sensor_readings
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    # Build query
    query = {
        "pond_id": pond_id,
        "timestamp": {"$gte": start_time, "$lte": end_time}
    }
    
    # Build projection based on requested parameters
    projection = {"_id": 0, "pond_id": 1, "timestamp": 1}
    if parameters:
        param_list = [p.strip() for p in parameters.split(',')]
        for param in param_list:
            projection[param] = 1
    else:
        # Include all sensor parameters
        projection.update({
            "ph": 1, "temperature": 1, "dissolved_oxygen": 1, "turbidity": 1,
            "nitrate": 1, "nitrite": 1, "ammonia": 1, "water_level": 1,
            "device_id": 1, "is_anomaly": 1
        })
    
    # Get readings
    readings = list(sensor_readings.find(query, projection).sort("timestamp", 1))
    
    if not readings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sensor data found for pond {pond_id} in the last {hours} hours"
        )
    
    return {
        "pond_id": pond_id,
        "time_range": {
            "start": start_time,
            "end": end_time,
            "hours": hours
        },
        "total_readings": len(readings),
        "readings": readings
    }


@router.get("/realtime")
async def get_realtime_data(
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get real-time data for all ponds (last 5 minutes)"""
    
    sensor_readings = db.sensor_readings
    
    # Get data from last 5 minutes
    time_threshold = datetime.utcnow() - timedelta(minutes=5)
    
    # Get latest reading for each pond
    pipeline = [
        {"$match": {"timestamp": {"$gte": time_threshold}}},
        {"$sort": {"timestamp": -1}},
        {"$group": {
            "_id": "$pond_id",
            "latest": {"$first": "$$ROOT"}
        }}
    ]
    
    latest_readings = list(sensor_readings.aggregate(pipeline))
    
    realtime_data = []
    for result in latest_readings:
        reading = result['latest']
        realtime_data.append({
            "pond_id": reading['pond_id'],
            "device_id": reading.get('device_id'),
            "timestamp": reading['timestamp'],
            "ph": reading.get('ph'),
            "temperature": reading.get('temperature'),
            "dissolved_oxygen": reading.get('dissolved_oxygen'),
            "turbidity": reading.get('turbidity'),
            "nitrate": reading.get('nitrate'),
            "nitrite": reading.get('nitrite'),
            "ammonia": reading.get('ammonia'),
            "water_level": reading.get('water_level'),
            "is_anomaly": reading.get('is_anomaly', False),
            "time_ago_seconds": int((datetime.utcnow() - reading['timestamp']).total_seconds())
        })
    
    return {
        "timestamp": datetime.utcnow(),
        "total_active_ponds": len(realtime_data),
        "data": realtime_data
    }
