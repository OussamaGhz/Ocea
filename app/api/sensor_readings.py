from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.database.connection import get_database
from app.services.database_service import SensorReadingService, PondService, FarmService
from app.schemas.schemas import SensorReadingCreate, SensorReadingResponse
from app.auth.auth import get_current_active_user
from app.models.models import User

router = APIRouter(prefix="/sensor-readings", tags=["Sensor Readings"])


@router.post("/", response_model=SensorReadingResponse)
async def create_sensor_reading(
    reading_data: SensorReadingCreate,
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new sensor reading (manual entry)"""
    reading_service = SensorReadingService(db)
    pond_service = PondService(db)
    farm_service = FarmService(db)
    
    # Check if pond exists and user has permission
    pond = await pond_service.get_pond_by_pond_id(reading_data.pond_id)
    if pond:
        farm = await farm_service.get_farm_by_id(str(pond.farm_id))
        if not current_user.is_admin and str(farm.owner_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to add readings for this pond"
            )
    
    reading = await reading_service.create_reading(reading_data)
    return SensorReadingResponse(
        id=str(reading.id),
        pond_id=reading.pond_id,
        timestamp=reading.timestamp,
        temperature=reading.temperature,
        ph=reading.ph,
        dissolved_oxygen=reading.dissolved_oxygen,
        turbidity=reading.turbidity,
        ammonia=reading.ammonia,
        nitrite=reading.nitrite,
        nitrate=reading.nitrate,
        salinity=reading.salinity,
        water_level=reading.water_level,
        is_anomaly=reading.is_anomaly,
        anomaly_score=reading.anomaly_score,
        anomaly_reasons=reading.anomaly_reasons,
        created_at=reading.created_at
    )


@router.get("/pond/{pond_id}", response_model=List[SensorReadingResponse])
async def get_readings_by_pond(
    pond_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get sensor readings by pond ID"""
    reading_service = SensorReadingService(db)
    pond_service = PondService(db)
    farm_service = FarmService(db)
    
    # Check if pond exists and user has permission
    pond = await pond_service.get_pond_by_pond_id(pond_id)
    if pond:
        farm = await farm_service.get_farm_by_id(str(pond.farm_id))
        if not current_user.is_admin and str(farm.owner_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access readings for this pond"
            )
    
    readings = await reading_service.get_readings_by_pond(
        pond_id, start_date, end_date, skip, limit
    )
    
    return [
        SensorReadingResponse(
            id=str(reading.id),
            pond_id=reading.pond_id,
            timestamp=reading.timestamp,
            temperature=reading.temperature,
            ph=reading.ph,
            dissolved_oxygen=reading.dissolved_oxygen,
            turbidity=reading.turbidity,
            ammonia=reading.ammonia,
            nitrite=reading.nitrite,
            nitrate=reading.nitrate,
            salinity=reading.salinity,
            water_level=reading.water_level,
            is_anomaly=reading.is_anomaly,
            anomaly_score=reading.anomaly_score,
            anomaly_reasons=reading.anomaly_reasons,
            created_at=reading.created_at
        )
        for reading in readings
    ]


@router.get("/pond/{pond_id}/latest", response_model=SensorReadingResponse)
async def get_latest_reading_by_pond(
    pond_id: str,
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get latest sensor reading for a pond"""
    reading_service = SensorReadingService(db)
    pond_service = PondService(db)
    farm_service = FarmService(db)
    
    # Check if pond exists and user has permission
    pond = await pond_service.get_pond_by_pond_id(pond_id)
    if pond:
        farm = await farm_service.get_farm_by_id(str(pond.farm_id))
        if not current_user.is_admin and str(farm.owner_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access readings for this pond"
            )
    
    reading = await reading_service.get_latest_reading_by_pond(pond_id)
    if not reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No readings found for this pond"
        )
    
    return SensorReadingResponse(
        id=str(reading.id),
        pond_id=reading.pond_id,
        timestamp=reading.timestamp,
        temperature=reading.temperature,
        ph=reading.ph,
        dissolved_oxygen=reading.dissolved_oxygen,
        turbidity=reading.turbidity,
        ammonia=reading.ammonia,
        nitrite=reading.nitrite,
        nitrate=reading.nitrate,
        salinity=reading.salinity,
        water_level=reading.water_level,
        is_anomaly=reading.is_anomaly,
        anomaly_score=reading.anomaly_score,
        anomaly_reasons=reading.anomaly_reasons,
        created_at=reading.created_at
    )


@router.get("/{reading_id}", response_model=SensorReadingResponse)
async def get_reading(
    reading_id: str,
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get sensor reading by ID"""
    reading_service = SensorReadingService(db)
    pond_service = PondService(db)
    farm_service = FarmService(db)
    
    reading = await reading_service.get_reading_by_id(reading_id)
    if not reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading not found"
        )
    
    # Check if user has permission to access this reading
    pond = await pond_service.get_pond_by_pond_id(reading.pond_id)
    if pond:
        farm = await farm_service.get_farm_by_id(str(pond.farm_id))
        if not current_user.is_admin and str(farm.owner_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this reading"
            )
    
    return SensorReadingResponse(
        id=str(reading.id),
        pond_id=reading.pond_id,
        timestamp=reading.timestamp,
        temperature=reading.temperature,
        ph=reading.ph,
        dissolved_oxygen=reading.dissolved_oxygen,
        turbidity=reading.turbidity,
        ammonia=reading.ammonia,
        nitrite=reading.nitrite,
        nitrate=reading.nitrate,
        salinity=reading.salinity,
        water_level=reading.water_level,
        is_anomaly=reading.is_anomaly,
        anomaly_score=reading.anomaly_score,
        anomaly_reasons=reading.anomaly_reasons,
        created_at=reading.created_at
    )
