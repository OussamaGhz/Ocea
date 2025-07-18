from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.database.connection import get_database
from app.services.database_service import AlertService, PondService, FarmService
from app.schemas.schemas import AlertCreate, AlertResponse, AlertUpdate
from app.auth.auth import get_current_active_user
from app.models.models import User

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.post("/", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new alert"""
    alert_service = AlertService(db)
    pond_service = PondService(db)
    farm_service = FarmService(db)
    
    # Check if pond exists and user has permission
    pond = await pond_service.get_pond_by_pond_id(alert_data.pond_id)
    if pond:
        farm = await farm_service.get_farm_by_id(str(pond.farm_id))
        if not current_user.is_admin and str(farm.owner_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create alerts for this pond"
            )
    
    alert = await alert_service.create_alert(alert_data)
    return AlertResponse(
        id=str(alert.id),
        pond_id=alert.pond_id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        title=alert.title,
        message=alert.message,
        sensor_reading_id=str(alert.sensor_reading_id) if alert.sensor_reading_id else None,
        is_acknowledged=alert.is_acknowledged,
        acknowledged_by=str(alert.acknowledged_by) if alert.acknowledged_by else None,
        acknowledged_at=alert.acknowledged_at,
        created_at=alert.created_at
    )


@router.get("/pond/{pond_id}", response_model=List[AlertResponse])
async def get_alerts_by_pond(
    pond_id: str,
    acknowledged: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get alerts by pond ID"""
    alert_service = AlertService(db)
    pond_service = PondService(db)
    farm_service = FarmService(db)
    
    # Check if pond exists and user has permission
    pond = await pond_service.get_pond_by_pond_id(pond_id)
    if pond:
        farm = await farm_service.get_farm_by_id(str(pond.farm_id))
        if not current_user.is_admin and str(farm.owner_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access alerts for this pond"
            )
    
    alerts = await alert_service.get_alerts_by_pond(pond_id, acknowledged, skip, limit)
    
    return [
        AlertResponse(
            id=str(alert.id),
            pond_id=alert.pond_id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            title=alert.title,
            message=alert.message,
            sensor_reading_id=str(alert.sensor_reading_id) if alert.sensor_reading_id else None,
            is_acknowledged=alert.is_acknowledged,
            acknowledged_by=str(alert.acknowledged_by) if alert.acknowledged_by else None,
            acknowledged_at=alert.acknowledged_at,
            created_at=alert.created_at
        )
        for alert in alerts
    ]


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get alert by ID"""
    alert_service = AlertService(db)
    pond_service = PondService(db)
    farm_service = FarmService(db)
    
    alert = await alert_service.get_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Check if user has permission to access this alert
    pond = await pond_service.get_pond_by_pond_id(alert.pond_id)
    if pond:
        farm = await farm_service.get_farm_by_id(str(pond.farm_id))
        if not current_user.is_admin and str(farm.owner_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this alert"
            )
    
    return AlertResponse(
        id=str(alert.id),
        pond_id=alert.pond_id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        title=alert.title,
        message=alert.message,
        sensor_reading_id=str(alert.sensor_reading_id) if alert.sensor_reading_id else None,
        is_acknowledged=alert.is_acknowledged,
        acknowledged_by=str(alert.acknowledged_by) if alert.acknowledged_by else None,
        acknowledged_at=alert.acknowledged_at,
        created_at=alert.created_at
    )


@router.put("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: str,
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Acknowledge an alert"""
    alert_service = AlertService(db)
    pond_service = PondService(db)
    farm_service = FarmService(db)
    
    # Check if alert exists
    existing_alert = await alert_service.get_alert_by_id(alert_id)
    if not existing_alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Check if user has permission
    pond = await pond_service.get_pond_by_pond_id(existing_alert.pond_id)
    if pond:
        farm = await farm_service.get_farm_by_id(str(pond.farm_id))
        if not current_user.is_admin and str(farm.owner_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to acknowledge this alert"
            )
    
    alert = await alert_service.acknowledge_alert(alert_id, str(current_user.id))
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    return AlertResponse(
        id=str(alert.id),
        pond_id=alert.pond_id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        title=alert.title,
        message=alert.message,
        sensor_reading_id=str(alert.sensor_reading_id) if alert.sensor_reading_id else None,
        is_acknowledged=alert.is_acknowledged,
        acknowledged_by=str(alert.acknowledged_by) if alert.acknowledged_by else None,
        acknowledged_at=alert.acknowledged_at,
        created_at=alert.created_at
    )
