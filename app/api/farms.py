from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.database.connection import get_database
from app.services.database_service import FarmService
from app.schemas.schemas import FarmCreate, FarmUpdate, FarmResponse
from app.auth.auth import get_current_active_user
from app.models.models import User

router = APIRouter(prefix="/farms", tags=["Farms"])


@router.post("/", response_model=FarmResponse)
async def create_farm(
    farm_data: FarmCreate,
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new farm"""
    farm_service = FarmService(db)
    
    farm = await farm_service.create_farm(farm_data, str(current_user.id))
    return FarmResponse(
        id=str(farm.id),
        name=farm.name,
        location=farm.location,
        owner_id=str(farm.owner_id),
        description=farm.description,
        created_at=farm.created_at,
        updated_at=farm.updated_at
    )


@router.get("/", response_model=List[FarmResponse])
async def get_farms(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's farms"""
    farm_service = FarmService(db)
    farms = await farm_service.get_farms_by_owner(str(current_user.id), skip=skip, limit=limit)
    
    return [
        FarmResponse(
            id=str(farm.id),
            name=farm.name,
            location=farm.location,
            owner_id=str(farm.owner_id),
            description=farm.description,
            created_at=farm.created_at,
            updated_at=farm.updated_at
        )
        for farm in farms
    ]


@router.get("/{farm_id}", response_model=FarmResponse)
async def get_farm(
    farm_id: str,
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get farm by ID"""
    farm_service = FarmService(db)
    farm = await farm_service.get_farm_by_id(farm_id)
    
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found"
        )
    
    # Check ownership (unless admin)
    if not current_user.is_admin and str(farm.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this farm"
        )
    
    return FarmResponse(
        id=str(farm.id),
        name=farm.name,
        location=farm.location,
        owner_id=str(farm.owner_id),
        description=farm.description,
        created_at=farm.created_at,
        updated_at=farm.updated_at
    )


@router.put("/{farm_id}", response_model=FarmResponse)
async def update_farm(
    farm_id: str,
    farm_data: FarmUpdate,
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Update farm"""
    farm_service = FarmService(db)
    
    # Check if farm exists and user has permission
    existing_farm = await farm_service.get_farm_by_id(farm_id)
    if not existing_farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found"
        )
    
    if not current_user.is_admin and str(existing_farm.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this farm"
        )
    
    farm = await farm_service.update_farm(farm_id, farm_data)
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found"
        )
    
    return FarmResponse(
        id=str(farm.id),
        name=farm.name,
        location=farm.location,
        owner_id=str(farm.owner_id),
        description=farm.description,
        created_at=farm.created_at,
        updated_at=farm.updated_at
    )


@router.delete("/{farm_id}")
async def delete_farm(
    farm_id: str,
    db=Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Delete farm"""
    farm_service = FarmService(db)
    
    # Check if farm exists and user has permission
    existing_farm = await farm_service.get_farm_by_id(farm_id)
    if not existing_farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found"
        )
    
    if not current_user.is_admin and str(existing_farm.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this farm"
        )
    
    success = await farm_service.delete_farm(farm_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found"
        )
    
    return {"message": "Farm deleted successfully"}
