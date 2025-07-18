from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.database.connection import get_database
from app.services.database_service import PondService, FarmService
from app.schemas.schemas import PondCreate, PondUpdate, PondResponse
from app.auth.auth import get_current_active_user
from app.models.models import User

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
