from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId
from enum import Enum


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, field=None):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema, handler):
        field_schema.update(type="string")
        return field_schema


class User(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Farm(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    location: str
    owner_id: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Pond(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., min_length=1, max_length=100)
    farm_id: PyObjectId
    description: Optional[str] = None
    size: Optional[float] = None  # in square meters
    depth: Optional[float] = None  # in meters
    fish_species: Optional[str] = None
    fish_count: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SensorReading(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    pond_id: str  # Simple string identifier like "pond_001", "pond_002"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Core sensor data as required
    ph: Optional[float] = None                    # pH level
    temperature: Optional[float] = None           # Temperature in Celsius
    dissolved_oxygen: Optional[float] = None      # Dissolved Oxygen in mg/L
    turbidity: Optional[float] = None             # Turbidity in NTU
    nitrate: Optional[float] = None               # Nitrate in mg/L
    nitrite: Optional[float] = None               # Nitrite in mg/L
    ammonia: Optional[float] = None               # Ammonia in mg/L
    water_level: Optional[float] = None           # Water level in meters
    
    # Metadata
    device_id: Optional[str] = None
    is_anomaly: bool = False
    anomaly_score: Optional[float] = None
    anomaly_reasons: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Alert(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    pond_id: str  # Simple string like "pond_001"
    sensor_reading_id: Optional[PyObjectId] = None
    alert_type: str  # e.g., "temperature_high", "ph_low", "oxygen_critical"
    parameter: str  # sensor parameter name
    current_value: float  # actual sensor value
    threshold_value: float  # threshold that was exceeded
    severity: AlertSeverity
    message: str
    is_resolved: bool = False
    sms_sent: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None


# Request/Response models for API
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
