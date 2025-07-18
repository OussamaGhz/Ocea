from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.models import User, Farm, Pond, SensorReading, Alert
from app.schemas.schemas import (
    UserCreate, UserUpdate, FarmCreate, FarmUpdate, 
    PondCreate, PondUpdate, SensorReadingCreate, AlertCreate
)
from app.auth.auth import get_password_hash


class UserService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.users

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if username or email already exists
        existing_user = await self.collection.find_one({
            "$or": [{"username": user_data.username}, {"email": user_data.email}]
        })
        if existing_user:
            raise ValueError("Username or email already exists")
        
        user_dict = user_data.dict()
        user_dict["hashed_password"] = get_password_hash(user_data.password)
        del user_dict["password"]
        
        result = await self.collection.insert_one(user_dict)
        user_dict["_id"] = result.inserted_id
        return User(**user_dict)

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        user_data = await self.collection.find_one({"_id": ObjectId(user_id)})
        return User(**user_data) if user_data else None

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get list of users"""
        cursor = self.collection.find().skip(skip).limit(limit)
        users = []
        async for user_data in cursor:
            users.append(User(**user_data))
        return users

    async def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """Update user"""
        update_data = {k: v for k, v in user_data.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)}, 
            {"$set": update_data}
        )
        
        if result.modified_count:
            return await self.get_user_by_id(user_id)
        return None

    async def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        result = await self.collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0


class FarmService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.farms

    async def create_farm(self, farm_data: FarmCreate, owner_id: str) -> Farm:
        """Create a new farm"""
        farm_dict = farm_data.dict()
        farm_dict["owner_id"] = ObjectId(owner_id)
        
        result = await self.collection.insert_one(farm_dict)
        farm_dict["_id"] = result.inserted_id
        return Farm(**farm_dict)

    async def get_farm_by_id(self, farm_id: str) -> Optional[Farm]:
        """Get farm by ID"""
        farm_data = await self.collection.find_one({"_id": ObjectId(farm_id)})
        return Farm(**farm_data) if farm_data else None

    async def get_farms_by_owner(self, owner_id: str, skip: int = 0, limit: int = 100) -> List[Farm]:
        """Get farms by owner"""
        cursor = self.collection.find({"owner_id": ObjectId(owner_id)}).skip(skip).limit(limit)
        farms = []
        async for farm_data in cursor:
            farms.append(Farm(**farm_data))
        return farms

    async def update_farm(self, farm_id: str, farm_data: FarmUpdate) -> Optional[Farm]:
        """Update farm"""
        update_data = {k: v for k, v in farm_data.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        
        result = await self.collection.update_one(
            {"_id": ObjectId(farm_id)}, 
            {"$set": update_data}
        )
        
        if result.modified_count:
            return await self.get_farm_by_id(farm_id)
        return None

    async def delete_farm(self, farm_id: str) -> bool:
        """Delete farm"""
        result = await self.collection.delete_one({"_id": ObjectId(farm_id)})
        return result.deleted_count > 0


class PondService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.ponds

    async def create_pond(self, pond_data: PondCreate) -> Pond:
        """Create a new pond"""
        pond_dict = pond_data.dict()
        pond_dict["farm_id"] = ObjectId(pond_data.farm_id)
        
        result = await self.collection.insert_one(pond_dict)
        pond_dict["_id"] = result.inserted_id
        return Pond(**pond_dict)

    async def get_pond_by_id(self, pond_id: str) -> Optional[Pond]:
        """Get pond by ID"""
        pond_data = await self.collection.find_one({"_id": ObjectId(pond_id)})
        return Pond(**pond_data) if pond_data else None

    async def get_ponds_by_farm(self, farm_id: str, skip: int = 0, limit: int = 100) -> List[Pond]:
        """Get ponds by farm"""
        cursor = self.collection.find({"farm_id": ObjectId(farm_id)}).skip(skip).limit(limit)
        ponds = []
        async for pond_data in cursor:
            ponds.append(Pond(**pond_data))
        return ponds

    async def update_pond(self, pond_id: str, pond_data: PondUpdate) -> Optional[Pond]:
        """Update pond"""
        update_data = {k: v for k, v in pond_data.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        
        result = await self.collection.update_one(
            {"_id": ObjectId(pond_id)}, 
            {"$set": update_data}
        )
        
        if result.modified_count:
            return await self.get_pond_by_id(pond_id)
        return None

    async def delete_pond(self, pond_id: str) -> bool:
        """Delete pond"""
        result = await self.collection.delete_one({"_id": ObjectId(pond_id)})
        return result.deleted_count > 0


class SensorReadingService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.sensor_readings

    async def create_reading(self, reading_data: SensorReadingCreate) -> SensorReading:
        """Create a new sensor reading"""
        reading_dict = reading_data.dict()
        if not reading_dict.get("timestamp"):
            reading_dict["timestamp"] = datetime.utcnow()
        
        # Add created_at field
        reading_dict["created_at"] = datetime.utcnow()
        
        # Convert pond_id string to ObjectId if it's a valid ObjectId string
        pond_id = reading_dict.get("pond_id")
        if isinstance(pond_id, str):
            if ObjectId.is_valid(pond_id):
                reading_dict["pond_id"] = ObjectId(pond_id)
            else:
                # If it's not a valid ObjectId, we'll create a dummy ObjectId or handle it differently
                # For now, let's create a new ObjectId from the string hash
                import hashlib
                hash_object = hashlib.md5(pond_id.encode())
                hex_dig = hash_object.hexdigest()
                # Create a valid ObjectId from the hash (take first 24 characters)
                reading_dict["pond_id"] = ObjectId(hex_dig[:24])
        
        result = await self.collection.insert_one(reading_dict)
        reading_dict["_id"] = result.inserted_id
        return SensorReading(**reading_dict)

    async def get_reading_by_id(self, reading_id: str) -> Optional[SensorReading]:
        """Get reading by ID"""
        reading_data = await self.collection.find_one({"_id": ObjectId(reading_id)})
        return SensorReading(**reading_data) if reading_data else None

    async def get_readings_by_pond(
        self, 
        pond_id: str, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[SensorReading]:
        """Get readings by pond with optional date filtering"""
        query = {"pond_id": ObjectId(pond_id)}
        
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            query["timestamp"] = date_filter
        
        cursor = self.collection.find(query).sort("timestamp", -1).skip(skip).limit(limit)
        readings = []
        async for reading_data in cursor:
            readings.append(SensorReading(**reading_data))
        return readings

    async def get_latest_reading_by_pond(self, pond_id: str) -> Optional[SensorReading]:
        """Get latest reading for a pond"""
        reading_data = await self.collection.find_one(
            {"pond_id": ObjectId(pond_id)}, 
            sort=[("timestamp", -1)]
        )
        return SensorReading(**reading_data) if reading_data else None

    async def update_reading_anomaly(
        self, 
        reading_id: str, 
        is_anomaly: bool, 
        anomaly_score: Optional[float] = None,
        anomaly_reasons: Optional[List[str]] = None
    ) -> Optional[SensorReading]:
        """Update reading anomaly status"""
        update_data = {
            "is_anomaly": is_anomaly,
            "anomaly_score": anomaly_score,
            "anomaly_reasons": anomaly_reasons or []
        }
        
        result = await self.collection.update_one(
            {"_id": ObjectId(reading_id)}, 
            {"$set": update_data}
        )
        
        if result.modified_count:
            return await self.get_reading_by_id(reading_id)
        return None


class AlertService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.alerts

    async def create_alert(self, alert_data: AlertCreate) -> Alert:
        """Create a new alert"""
        alert_dict = alert_data.dict()
        if alert_data.sensor_reading_id:
            alert_dict["sensor_reading_id"] = ObjectId(alert_data.sensor_reading_id)
        
        result = await self.collection.insert_one(alert_dict)
        alert_dict["_id"] = result.inserted_id
        return Alert(**alert_dict)

    async def get_alert_by_id(self, alert_id: str) -> Optional[Alert]:
        """Get alert by ID"""
        alert_data = await self.collection.find_one({"_id": ObjectId(alert_id)})
        return Alert(**alert_data) if alert_data else None

    async def get_alerts_by_pond(
        self, 
        pond_id: str, 
        acknowledged: Optional[bool] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Alert]:
        """Get alerts by pond"""
        query = {"pond_id": ObjectId(pond_id)}
        if acknowledged is not None:
            query["is_acknowledged"] = acknowledged
        
        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        alerts = []
        async for alert_data in cursor:
            alerts.append(Alert(**alert_data))
        return alerts

    async def acknowledge_alert(self, alert_id: str, user_id: str) -> Optional[Alert]:
        """Acknowledge an alert"""
        update_data = {
            "is_acknowledged": True,
            "acknowledged_by": ObjectId(user_id),
            "acknowledged_at": datetime.utcnow()
        }
        
        result = await self.collection.update_one(
            {"_id": ObjectId(alert_id)}, 
            {"$set": update_data}
        )
        
        if result.modified_count:
            return await self.get_alert_by_id(alert_id)
        return None
