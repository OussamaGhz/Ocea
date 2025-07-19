from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# User Schemas
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = Field(None, pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime


class UserLogin(BaseModel):
    username: str
    password: str


# Farm Schemas
class FarmCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class FarmUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None


class FarmResponse(BaseModel):
    id: str
    name: str
    location: str
    owner_id: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime


# Pond Schemas
class PondCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    farm_id: str
    description: Optional[str] = None
    size: Optional[float] = None  # in square meters
    depth: Optional[float] = None  # in meters
    fish_species: Optional[str] = None
    fish_count: Optional[int] = None


class PondUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    size: Optional[float] = None
    depth: Optional[float] = None
    fish_species: Optional[str] = None
    fish_count: Optional[int] = None


class PondResponse(BaseModel):
    id: str
    name: str
    farm_id: str
    description: Optional[str]
    size: Optional[float]
    depth: Optional[float]
    fish_species: Optional[str]
    fish_count: Optional[int]
    created_at: datetime
    updated_at: datetime


# Sensor Reading Schemas
class SensorReadingCreate(BaseModel):
    pond_id: str
    timestamp: Optional[datetime] = None
    
    # Core sensor data as required
    ph: Optional[float] = None                    # pH level
    temperature: Optional[float] = None           # Temperature in Celsius
    dissolved_oxygen: Optional[float] = None      # Dissolved Oxygen in mg/L
    turbidity: Optional[float] = None             # Turbidity in NTU
    nitrate: Optional[float] = None               # Nitrate in mg/L
    nitrite: Optional[float] = None               # Nitrite in mg/L
    ammonia: Optional[float] = None               # Ammonia in mg/L
    water_level: Optional[float] = None           # Water level in meters
    
    device_id: Optional[str] = None


class SensorReadingResponse(BaseModel):
    id: str
    pond_id: str
    timestamp: datetime
    ph: Optional[float]
    temperature: Optional[float]
    dissolved_oxygen: Optional[float]
    turbidity: Optional[float]
    nitrate: Optional[float]
    nitrite: Optional[float]
    ammonia: Optional[float]
    water_level: Optional[float]
    device_id: Optional[str]
    is_anomaly: bool
    anomaly_score: Optional[float]
    anomaly_reasons: Optional[List[str]]
    created_at: datetime


# Alert Schemas
class AlertCreate(BaseModel):
    pond_id: str
    alert_type: str
    severity: str
    title: str
    message: str
    sensor_reading_id: Optional[str] = None


class AlertUpdate(BaseModel):
    is_acknowledged: Optional[bool] = None


class AlertResponse(BaseModel):
    id: str
    pond_id: str
    alert_type: str
    severity: str
    title: str
    message: str
    sensor_reading_id: Optional[str]
    is_acknowledged: bool
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]
    created_at: datetime


# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# Query Schemas
class DateRangeQuery(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    pond_id: Optional[str] = None


class PaginationQuery(BaseModel):
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)
