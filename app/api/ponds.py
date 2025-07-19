from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.database.connection import get_database
from app.services.database_service import SensorReadingService, PondService, FarmService
from app.schemas.schemas import PondCreate, PondUpdate, PondResponse
from app.auth.auth import get_current_active_user
from app.models.models import User
from pydantic import BaseModel

router = APIRouter(prefix="/ponds", tags=["Ponds"])


@router.post("/", response_model=PondResponse)
async def create_pond(
    pond_data: PondCreate,
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new pond"""
    pond_service = PondService(db)
    farm_service = FarmService(db)
    
    # Check if farm exists and user has permission
    farm = await farm_service.get_farm_by_id(pond_data.farm_id)
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found"
        )
    
    if not current_user.is_admin and str(farm.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create ponds in this farm"
        )
    
    try:
        pond = await pond_service.create_pond(pond_data)
        return PondResponse(
            id=str(pond.id),
            name=pond.name,
            farm_id=str(pond.farm_id),
            description=pond.description,
            size=pond.size,
            depth=pond.depth,
            fish_species=pond.fish_species,
            fish_count=pond.fish_count,
            created_at=pond.created_at,
            updated_at=pond.updated_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/farm/{farm_id}", response_model=List[PondResponse])
async def get_ponds_by_farm(
    farm_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get ponds by farm"""
    pond_service = PondService(db)
    farm_service = FarmService(db)
    
    # Check if farm exists and user has permission
    farm = await farm_service.get_farm_by_id(farm_id)
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found"
        )
    
    if not current_user.is_admin and str(farm.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access ponds in this farm"
        )
    
    ponds = await pond_service.get_ponds_by_farm(farm_id, skip=skip, limit=limit)
    
    return [
        PondResponse(
            id=str(pond.id),
            pond_id=pond.pond_id,
            name=pond.name,
            farm_id=str(pond.farm_id),
            area=pond.area,
            depth=pond.depth,
            fish_species=pond.fish_species,
            created_at=pond.created_at,
            updated_at=pond.updated_at
        )
        for pond in ponds
    ]


@router.get("/{pond_id}", response_model=PondResponse)
async def get_pond(
    pond_id: str,
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get pond by ID"""
    pond_service = PondService(db)
    farm_service = FarmService(db)
    
    pond = await pond_service.get_pond_by_id(pond_id)
    if not pond:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pond not found"
        )
    
    # Check farm ownership
    farm = await farm_service.get_farm_by_id(str(pond.farm_id))
    if not current_user.is_admin and str(farm.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this pond"
        )
    
    return PondResponse(
        id=str(pond.id),
        pond_id=pond.pond_id,
        name=pond.name,
        farm_id=str(pond.farm_id),
        area=pond.area,
        depth=pond.depth,
        fish_species=pond.fish_species,
        created_at=pond.created_at,
        updated_at=pond.updated_at
    )


@router.put("/{pond_id}", response_model=PondResponse)
async def update_pond(
    pond_id: str,
    pond_data: PondUpdate,
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Update pond"""
    pond_service = PondService(db)
    farm_service = FarmService(db)
    
    # Check if pond exists
    existing_pond = await pond_service.get_pond_by_id(pond_id)
    if not existing_pond:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pond not found"
        )
    
    # Check farm ownership
    farm = await farm_service.get_farm_by_id(str(existing_pond.farm_id))
    if not current_user.is_admin and str(farm.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this pond"
        )
    
    pond = await pond_service.update_pond(pond_id, pond_data)
    if not pond:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pond not found"
        )
    
    return PondResponse(
        id=str(pond.id),
        pond_id=pond.pond_id,
        name=pond.name,
        farm_id=str(pond.farm_id),
        area=pond.area,
        depth=pond.depth,
        fish_species=pond.fish_species,
        created_at=pond.created_at,
        updated_at=pond.updated_at
    )


@router.delete("/{pond_id}")
async def delete_pond(
    pond_id: str,
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Delete pond"""
    pond_service = PondService(db)
    farm_service = FarmService(db)
    
    # Check if pond exists
    existing_pond = await pond_service.get_pond_by_id(pond_id)
    if not existing_pond:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pond not found"
        )
    
    # Check farm ownership
    farm = await farm_service.get_farm_by_id(str(existing_pond.farm_id))
    if not current_user.is_admin and str(farm.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this pond"
        )
    
    success = await pond_service.delete_pond(pond_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pond not found"
        )
    
    return {"message": "Pond deleted successfully"}


# Enhanced pond management routes with sensor data integration

class PondWithSensorData(BaseModel):
    # Pond information
    id: str
    name: str
    farm_id: str
    description: Optional[str] = None
    size: Optional[float] = None
    depth: Optional[float] = None
    fish_species: Optional[str] = None
    fish_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    # Sensor data integration
    latest_reading: Optional[dict] = None
    sensor_status: str = "unknown"  # active, inactive, warning, error
    last_data_time: Optional[datetime] = None
    total_readings_today: int = 0
    anomaly_count_today: int = 0
    avg_ph_today: Optional[float] = None
    avg_temperature_today: Optional[float] = None
    avg_dissolved_oxygen_today: Optional[float] = None


@router.get("/management/overview", response_model=List[PondWithSensorData])
async def get_ponds_management_overview(
    farm_id: Optional[str] = Query(None, description="Filter by farm ID"),
    status_filter: Optional[str] = Query(None, description="Filter by sensor status: active, inactive, warning, error"),
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get comprehensive pond management overview with sensor data integration"""
    
    pond_service = PondService(db)
    farm_service = FarmService(db)
    sensor_readings = db.sensor_readings
    
    # Get ponds based on user permissions
    if current_user.is_admin:
        if farm_id:
            ponds = await pond_service.get_ponds_by_farm(farm_id)
        else:
            ponds = await pond_service.get_all_ponds()
    else:
        # Get user's farms
        user_farms = await farm_service.get_farms_by_owner(str(current_user.id))
        if farm_id:
            # Check if user owns the specified farm
            if farm_id not in [str(farm.id) for farm in user_farms]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this farm"
                )
            ponds = await pond_service.get_ponds_by_farm(farm_id)
        else:
            # Get all ponds from user's farms
            ponds = []
            for farm in user_farms:
                farm_ponds = await pond_service.get_ponds_by_farm(str(farm.id))
                ponds.extend(farm_ponds)
    
    # Time range for today's data
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    now = datetime.utcnow()
    
    result = []
    
    for pond in ponds:
        # For database ponds, we need to map to actual sensor data using pond_id
        # Assuming pond has a pond_id field that matches sensor data
        pond_id = getattr(pond, 'pond_id', pond.name.lower().replace(' ', '_'))
        
        # Get latest sensor reading
        latest_reading = sensor_readings.find_one(
            {"pond_id": pond_id},
            sort=[("timestamp", -1)]
        )
        
        # Get today's readings
        today_readings = list(sensor_readings.find({
            "pond_id": pond_id,
            "timestamp": {"$gte": today_start, "$lte": now}
        }))
        
        # Calculate sensor status
        sensor_status = "inactive"
        if latest_reading:
            time_since_last = (now - latest_reading['timestamp']).total_seconds() / 60  # minutes
            if time_since_last <= 15:
                sensor_status = "active"
            elif time_since_last <= 60:
                sensor_status = "warning"
            else:
                sensor_status = "error"
        
        # Calculate today's statistics
        total_readings_today = len(today_readings)
        anomaly_count_today = len([r for r in today_readings if r.get('is_anomaly')])
        
        # Calculate averages for today
        ph_values = [r.get('ph') for r in today_readings if r.get('ph') is not None]
        temp_values = [r.get('temperature') for r in today_readings if r.get('temperature') is not None]
        do_values = [r.get('dissolved_oxygen') for r in today_readings if r.get('dissolved_oxygen') is not None]
        
        avg_ph_today = sum(ph_values) / len(ph_values) if ph_values else None
        avg_temperature_today = sum(temp_values) / len(temp_values) if temp_values else None
        avg_dissolved_oxygen_today = sum(do_values) / len(do_values) if do_values else None
        
        # Create enhanced pond data
        pond_data = PondWithSensorData(
            id=str(pond.id),
            name=pond.name,
            farm_id=str(pond.farm_id),
            description=pond.description,
            size=pond.size,
            depth=pond.depth,
            fish_species=pond.fish_species,
            fish_count=pond.fish_count,
            created_at=pond.created_at,
            updated_at=pond.updated_at,
            latest_reading=latest_reading,
            sensor_status=sensor_status,
            last_data_time=latest_reading['timestamp'] if latest_reading else None,
            total_readings_today=total_readings_today,
            anomaly_count_today=anomaly_count_today,
            avg_ph_today=round(avg_ph_today, 2) if avg_ph_today else None,
            avg_temperature_today=round(avg_temperature_today, 2) if avg_temperature_today else None,
            avg_dissolved_oxygen_today=round(avg_dissolved_oxygen_today, 2) if avg_dissolved_oxygen_today else None
        )
        
        # Apply status filter
        if status_filter and sensor_status != status_filter:
            continue
            
        result.append(pond_data)
    
    return result


@router.get("/{pond_id}/management/details", response_model=PondWithSensorData)
async def get_pond_management_details(
    pond_id: str,
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed pond management information with sensor data"""
    
    pond_service = PondService(db)
    farm_service = FarmService(db)
    sensor_readings = db.sensor_readings
    
    # Get pond
    pond = await pond_service.get_pond_by_id(pond_id)
    if not pond:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pond not found"
        )
    
    # Check permissions
    if not current_user.is_admin:
        farm = await farm_service.get_farm_by_id(str(pond.farm_id))
        if str(farm.owner_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this pond"
            )
    
    # Map to sensor data
    sensor_pond_id = getattr(pond, 'pond_id', pond.name.lower().replace(' ', '_'))
    
    # Time range for today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    now = datetime.utcnow()
    
    # Get latest sensor reading
    latest_reading = sensor_readings.find_one(
        {"pond_id": sensor_pond_id},
        sort=[("timestamp", -1)]
    )
    
    # Get today's readings
    today_readings = list(sensor_readings.find({
        "pond_id": sensor_pond_id,
        "timestamp": {"$gte": today_start, "$lte": now}
    }))
    
    # Calculate sensor status
    sensor_status = "inactive"
    if latest_reading:
        time_since_last = (now - latest_reading['timestamp']).total_seconds() / 60
        if time_since_last <= 15:
            sensor_status = "active"
        elif time_since_last <= 60:
            sensor_status = "warning"
        else:
            sensor_status = "error"
    
    # Calculate statistics
    total_readings_today = len(today_readings)
    anomaly_count_today = len([r for r in today_readings if r.get('is_anomaly')])
    
    ph_values = [r.get('ph') for r in today_readings if r.get('ph') is not None]
    temp_values = [r.get('temperature') for r in today_readings if r.get('temperature') is not None]
    do_values = [r.get('dissolved_oxygen') for r in today_readings if r.get('dissolved_oxygen') is not None]
    
    return PondWithSensorData(
        id=str(pond.id),
        name=pond.name,
        farm_id=str(pond.farm_id),
        description=pond.description,
        size=pond.size,
        depth=pond.depth,
        fish_species=pond.fish_species,
        fish_count=pond.fish_count,
        created_at=pond.created_at,
        updated_at=pond.updated_at,
        latest_reading=latest_reading,
        sensor_status=sensor_status,
        last_data_time=latest_reading['timestamp'] if latest_reading else None,
        total_readings_today=total_readings_today,
        anomaly_count_today=anomaly_count_today,
        avg_ph_today=round(sum(ph_values) / len(ph_values), 2) if ph_values else None,
        avg_temperature_today=round(sum(temp_values) / len(temp_values), 2) if temp_values else None,
        avg_dissolved_oxygen_today=round(sum(do_values) / len(do_values), 2) if do_values else None
    )
