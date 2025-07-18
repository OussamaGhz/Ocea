from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")
        return field_schema


class User(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern="^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$")
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Farm(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=200)
    owner_id: PyObjectId
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Pond(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    pond_id: str = Field(..., min_length=1, max_length=50)  # External pond identifier
    name: str = Field(..., min_length=1, max_length=100)
    farm_id: PyObjectId
    area: Optional[float] = None  # in square meters
    depth: Optional[float] = None  # in meters
    fish_species: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class SensorReading(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    pond_id: str = Field(...)  # External pond identifier from MQTT
    timestamp: datetime = Field(...)
    temperature: Optional[float] = None  # Celsius
    ph: Optional[float] = None  # pH level
    dissolved_oxygen: Optional[float] = None  # mg/L
    turbidity: Optional[float] = None  # NTU
    ammonia: Optional[float] = None  # mg/L
    nitrite: Optional[float] = None  # mg/L
    nitrate: Optional[float] = None  # mg/L
    salinity: Optional[float] = None  # ppt
    water_level: Optional[float] = None  # cm
    is_anomaly: bool = False
    anomaly_score: Optional[float] = None
    anomaly_reasons: Optional[List[str]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Alert(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    pond_id: str = Field(...)
    alert_type: str = Field(...)  # 'anomaly', 'threshold', 'system'
    severity: str = Field(...)  # 'low', 'medium', 'high', 'critical'
    title: str = Field(...)
    message: str = Field(...)
    sensor_reading_id: Optional[PyObjectId] = None
    is_acknowledged: bool = False
    acknowledged_by: Optional[PyObjectId] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class SystemLog(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    level: str = Field(...)  # 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    module: str = Field(...)
    message: str = Field(...)
    details: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
