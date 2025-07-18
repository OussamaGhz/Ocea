#!/usr/bin/env python3
"""
Database Migration Script

This script handles database migrations and updates.
"""

import asyncio
from app.database.connection import connect_to_mongo, get_database, close_mongo_connection


async def migrate_v1_to_v2():
    """Example migration - add new fields to existing collections"""
    print("Running migration v1 to v2...")
    
    db = get_database()
    
    # Add new fields to sensor_readings if they don't exist
    await db.sensor_readings.update_many(
        {"anomaly_score": {"$exists": False}},
        {"$set": {"anomaly_score": None, "anomaly_reasons": []}}
    )
    
    # Add indexes for new fields
    await db.sensor_readings.create_index("is_anomaly")
    await db.sensor_readings.create_index("anomaly_score")
    
    print("Migration v1 to v2 completed")


async def main():
    """Main migration function"""
    print("🔄 Database Migration Tool")
    print("=" * 30)
    
    await connect_to_mongo()
    
    # Run migrations
    await migrate_v1_to_v2()
    
    await close_mongo_connection()
    
    print("✅ All migrations completed!")


if __name__ == "__main__":
    asyncio.run(main())
