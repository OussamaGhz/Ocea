"""
Database Seeder for MVP - Populate with Sample Data
"""
import asyncio
import logging
from datetime import datetime, timedelta
import random
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings
from app.models.models import AlertSeverity
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


class MVPDataSeeder:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            self.db = self.client[settings.database_name]
            logger.info(f"Connected to MongoDB: {settings.database_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            sys.exit(1)

    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()

    def generate_realistic_sensor_data(self, pond_id: str, timestamp: datetime):
        """Generate realistic sensor readings for a pond"""
        # Base values with slight variations
        base_values = {
            "pond_001": {
                "ph": 7.2,
                "temperature": 25.0,
                "dissolved_oxygen": 8.0,
                "turbidity": 3.0,
                "nitrate": 20.0,
                "nitrite": 0.2,
                "ammonia": 0.1,
                "water_level": 1.5
            },
            "pond_002": {
                "ph": 7.0,
                "temperature": 24.5,
                "dissolved_oxygen": 7.5,
                "turbidity": 4.0,
                "nitrate": 25.0,
                "nitrite": 0.3,
                "ammonia": 0.15,
                "water_level": 1.8
            },
            "pond_003": {
                "ph": 7.4,
                "temperature": 26.0,
                "dissolved_oxygen": 8.5,
                "turbidity": 2.5,
                "nitrate": 18.0,
                "nitrite": 0.1,
                "ammonia": 0.08,
                "water_level": 1.2
            }
        }

        base = base_values.get(pond_id, base_values["pond_001"])
        
        # Add realistic variations
        return {
            "pond_id": pond_id,
            "device_id": f"sensor_{pond_id.split('_')[1]}",
            "timestamp": timestamp,
            "ph": round(base["ph"] + random.uniform(-0.3, 0.3), 2),
            "temperature": round(base["temperature"] + random.uniform(-2.0, 2.0), 2),
            "dissolved_oxygen": round(base["dissolved_oxygen"] + random.uniform(-1.0, 1.0), 2),
            "turbidity": round(max(0, base["turbidity"] + random.uniform(-1.0, 1.0)), 2),
            "nitrate": round(max(0, base["nitrate"] + random.uniform(-5.0, 5.0)), 2),
            "nitrite": round(max(0, base["nitrite"] + random.uniform(-0.1, 0.1)), 3),
            "ammonia": round(max(0, base["ammonia"] + random.uniform(-0.05, 0.05)), 3),
            "water_level": round(max(0.1, base["water_level"] + random.uniform(-0.2, 0.2)), 2),
            "created_at": datetime.utcnow()
        }

    async def seed_users(self):
        """Create sample users"""
        logger.info("🧑‍💼 Seeding users...")
        
        users = [
            {
                "username": "admin",
                "email": "admin@pondmonitoring.com",
                "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # password: secret
                "is_active": True,
                "is_admin": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "username": "farmmanager",
                "email": "manager@pondmonitoring.com", 
                "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # password: secret
                "is_active": True,
                "is_admin": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]

        # Clear existing users
        await self.db.users.delete_many({})
        
        # Insert users
        result = await self.db.users.insert_many(users)
        logger.info(f"✅ Created {len(result.inserted_ids)} users")
        return result.inserted_ids

    async def seed_farms(self, owner_id):
        """Create sample farms"""
        logger.info("🚜 Seeding farms...")
        
        farms = [
            {
                "name": "Aqua Fresh Farm",
                "description": "Primary aquaculture facility with multiple pond systems",
                "location": "North Valley, CA",
                "owner_id": owner_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]

        # Clear existing farms
        await self.db.farms.delete_many({})
        
        # Insert farms
        result = await self.db.farms.insert_many(farms)
        logger.info(f"✅ Created {len(result.inserted_ids)} farms")
        return result.inserted_ids

    async def seed_ponds(self, farm_id):
        """Create sample ponds"""
        logger.info("🏊 Seeding ponds...")
        
        ponds = [
            {
                "name": "Main Production Pond",
                "farm_id": farm_id,
                "description": "Primary production pond for tilapia farming",
                "size": 1200.0,  # square meters
                "depth": 2.5,    # meters
                "fish_species": "Tilapia",
                "fish_count": 5000,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "name": "Secondary Pond",
                "farm_id": farm_id,
                "description": "Secondary pond for juvenile fish",
                "size": 800.0,
                "depth": 2.0,
                "fish_species": "Tilapia",
                "fish_count": 3000,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "name": "Quarantine Pond",
                "farm_id": farm_id,
                "description": "Isolation pond for new or sick fish",
                "size": 400.0,
                "depth": 1.8,
                "fish_species": "Mixed",
                "fish_count": 500,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]

        # Clear existing ponds
        await self.db.ponds.delete_many({})
        
        # Insert ponds
        result = await self.db.ponds.insert_many(ponds)
        logger.info(f"✅ Created {len(result.inserted_ids)} ponds")
        return result.inserted_ids

    async def seed_sensor_readings(self):
        """Create historical sensor readings"""
        logger.info("📊 Seeding sensor readings...")
        
        # Clear existing readings
        await self.db.sensor_readings.delete_many({})
        
        pond_ids = ["pond_001", "pond_002", "pond_003"]
        readings = []
        
        # Generate readings for the last 7 days
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=7)
        
        current_time = start_time
        while current_time <= end_time:
            for pond_id in pond_ids:
                reading = self.generate_realistic_sensor_data(pond_id, current_time)
                readings.append(reading)
            
            # Increment by 30 minutes
            current_time += timedelta(minutes=30)

        # Insert readings in batches
        batch_size = 1000
        total_inserted = 0
        
        for i in range(0, len(readings), batch_size):
            batch = readings[i:i + batch_size]
            result = await self.db.sensor_readings.insert_many(batch)
            total_inserted += len(result.inserted_ids)
            logger.info(f"📈 Inserted {len(result.inserted_ids)} readings (Total: {total_inserted})")
        
        logger.info(f"✅ Created {total_inserted} sensor readings across {len(pond_ids)} ponds")

    async def seed_alerts(self):
        """Create sample alerts"""
        logger.info("🚨 Seeding alerts...")
        
        # Clear existing alerts
        await self.db.alerts.delete_many({})
        
        alerts = []
        pond_ids = ["pond_001", "pond_002", "pond_003"]
        
        # Create various types of alerts
        alert_scenarios = [
            {
                "pond_id": "pond_001",
                "alert_type": "temperature_high",
                "parameter": "temperature",
                "current_value": 31.5,
                "threshold_value": 30.0,
                "severity": AlertSeverity.HIGH.value,
                "message": "HIGH: Temperature above threshold: 31.5 (limit: 30.0)",
                "is_resolved": False,
                "sms_sent": True,
                "created_at": datetime.utcnow() - timedelta(hours=2)
            },
            {
                "pond_id": "pond_002",
                "alert_type": "ph_low",
                "parameter": "ph",
                "current_value": 6.2,
                "threshold_value": 6.5,
                "severity": AlertSeverity.MEDIUM.value,
                "message": "MEDIUM: pH below threshold: 6.2 (limit: 6.5)",
                "is_resolved": True,
                "sms_sent": False,
                "created_at": datetime.utcnow() - timedelta(hours=6),
                "resolved_at": datetime.utcnow() - timedelta(hours=4)
            },
            {
                "pond_id": "pond_003",
                "alert_type": "dissolved_oxygen_low",
                "parameter": "dissolved_oxygen",
                "current_value": 4.2,
                "threshold_value": 5.0,
                "severity": AlertSeverity.HIGH.value,
                "message": "HIGH: Dissolved oxygen below threshold: 4.2 (limit: 5.0)",
                "is_resolved": False,
                "sms_sent": True,
                "created_at": datetime.utcnow() - timedelta(hours=1)
            },
            {
                "pond_id": "pond_001",
                "alert_type": "ammonia_high",
                "parameter": "ammonia",
                "current_value": 0.7,
                "threshold_value": 0.5,
                "severity": AlertSeverity.CRITICAL.value,
                "message": "CRITICAL: Ammonia above threshold: 0.7 (limit: 0.5)",
                "is_resolved": False,
                "sms_sent": True,
                "created_at": datetime.utcnow() - timedelta(minutes=30)
            },
            {
                "pond_id": "pond_002",
                "alert_type": "turbidity_high",
                "parameter": "turbidity",
                "current_value": 12.5,
                "threshold_value": 10.0,
                "severity": AlertSeverity.MEDIUM.value,
                "message": "MEDIUM: Turbidity above threshold: 12.5 (limit: 10.0)",
                "is_resolved": True,
                "sms_sent": False,
                "created_at": datetime.utcnow() - timedelta(days=1),
                "resolved_at": datetime.utcnow() - timedelta(hours=18)
            }
        ]

        result = await self.db.alerts.insert_many(alert_scenarios)
        logger.info(f"✅ Created {len(result.inserted_ids)} sample alerts")

    async def run_seeder(self):
        """Run complete database seeding process"""
        try:
            await self.connect()
            
            logger.info("🌱 Starting MVP database seeding...")
            
            # Seed users first
            user_ids = await self.seed_users()
            admin_id = user_ids[0]
            
            # Seed farms
            farm_ids = await self.seed_farms(admin_id)
            farm_id = farm_ids[0]
            
            # Seed ponds
            pond_ids = await self.seed_ponds(farm_id)
            
            # Seed sensor readings (lots of historical data)
            await self.seed_sensor_readings()
            
            # Seed alerts
            await self.seed_alerts()
            
            # Print summary
            await self.print_seeding_summary()
            
            logger.info("🎉 MVP database seeding completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Seeding failed: {e}")
            raise
        finally:
            await self.close()

    async def print_seeding_summary(self):
        """Print summary of seeded data"""
        logger.info("\n📋 SEEDING SUMMARY")
        logger.info("=" * 50)
        
        # Count documents
        users_count = await self.db.users.count_documents({})
        farms_count = await self.db.farms.count_documents({})
        ponds_count = await self.db.ponds.count_documents({})
        readings_count = await self.db.sensor_readings.count_documents({})
        alerts_count = await self.db.alerts.count_documents({})
        active_alerts = await self.db.alerts.count_documents({"is_resolved": False})
        
        logger.info(f"👥 Users: {users_count}")
        logger.info(f"🚜 Farms: {farms_count}")
        logger.info(f"🏊 Ponds: {ponds_count}")
        logger.info(f"📊 Sensor Readings: {readings_count}")
        logger.info(f"🚨 Total Alerts: {alerts_count}")
        logger.info(f"⚠️  Active Alerts: {active_alerts}")
        
        # Get latest readings
        latest_reading = await self.db.sensor_readings.find_one({}, sort=[("timestamp", -1)])
        if latest_reading:
            logger.info(f"📅 Latest Reading: {latest_reading['timestamp']}")
        
        logger.info("=" * 50)
        logger.info("🎯 MVP Dashboard is ready with sample data!")
        logger.info("\n🔗 Test your endpoints:")
        logger.info("   GET /mvp/dashboard/overview")
        logger.info("   GET /mvp/pond/pond_001/latest")
        logger.info("   GET /mvp/alerts/active")
        logger.info("\n🧑‍💼 Test Login:")
        logger.info("   Username: admin")
        logger.info("   Password: secret")


async def main():
    """Main function to run the seeder"""
    seeder = MVPDataSeeder()
    await seeder.run_seeder()


if __name__ == "__main__":
    asyncio.run(main())
