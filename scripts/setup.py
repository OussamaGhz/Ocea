#!/usr/bin/env python3
"""
Setup script for the Pond Monitoring System

This script helps with initial setup including:
- Creating environment file
- Setting up MongoDB indexes
- Creating initial admin user
"""

import asyncio
import os
import sys
from getpass import getpass

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings
from app.database.connection import connect_to_mongo, get_database, close_mongo_connection
from app.services.database_service import UserService
from app.schemas.schemas import UserCreate


async def setup_database():
    """Setup database indexes"""
    print("Setting up database indexes...")
    
    db = get_database()
    
    # Create indexes for better performance
    await db.users.create_index("username", unique=True)
    await db.users.create_index("email", unique=True)
    await db.farms.create_index("owner_id")
    await db.ponds.create_index("pond_id", unique=True)
    await db.ponds.create_index("farm_id")
    await db.sensor_readings.create_index([("pond_id", 1), ("timestamp", -1)])
    await db.sensor_readings.create_index("timestamp")
    await db.alerts.create_index([("pond_id", 1), ("created_at", -1)])
    await db.alerts.create_index("is_acknowledged")
    
    print("Database indexes created successfully!")


async def create_admin_user():
    """Create initial admin user"""
    print("\nCreating admin user...")
    
    username = input("Admin username: ").strip()
    if not username:
        print("Username cannot be empty")
        return False
    
    email = input("Admin email: ").strip()
    if not email:
        print("Email cannot be empty")
        return False
    
    password = getpass("Admin password: ").strip()
    if len(password) < 6:
        print("Password must be at least 6 characters")
        return False
    
    confirm_password = getpass("Confirm password: ").strip()
    if password != confirm_password:
        print("Passwords do not match")
        return False
    
    try:
        db = get_database()
        user_service = UserService(db)
        
        user_data = UserCreate(
            username=username,
            email=email,
            password=password
        )
        
        user = await user_service.create_user(user_data)
        
        # Make user admin
        await db.users.update_one(
            {"_id": user.id},
            {"$set": {"is_admin": True}}
        )
        
        print(f"Admin user '{username}' created successfully!")
        return True
        
    except ValueError as e:
        print(f"Error creating user: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def create_env_file():
    """Create .env file if it doesn't exist"""
    if os.path.exists(".env"):
        print(".env file already exists")
        return
    
    print("Creating .env file...")
    
    # Copy from example
    if os.path.exists(".env.example"):
        import shutil
        shutil.copy(".env.example", ".env")
        print(".env file created from .env.example")
        print("Please edit .env file with your configuration")
    else:
        print(".env.example not found, please create .env manually")


def create_models_directory():
    """Create models directory for ML models"""
    os.makedirs("models", exist_ok=True)
    print("Models directory created")


async def main():
    """Main setup function"""
    print("🐟 Pond Monitoring System Setup")
    print("=" * 40)
    
    # Create environment file
    create_env_file()
    
    # Create models directory
    create_models_directory()
    
    # Connect to database
    try:
        await connect_to_mongo()
        print("Connected to MongoDB successfully!")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        print("Please check your MongoDB connection settings in .env")
        return
    
    # Setup database
    await setup_database()
    
    # Create admin user
    create_admin = input("\nDo you want to create an admin user? (y/n): ").lower().strip()
    if create_admin in ['y', 'yes']:
        success = await create_admin_user()
        if not success:
            print("Failed to create admin user")
    
    # Close database connection
    await close_mongo_connection()
    
    print("\n✅ Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file with your configuration")
    print("2. Start the API server: uvicorn app.main:app --reload")
    print("3. Start the MQTT subscriber: python -m app.mqtt.subscriber")
    print("4. Visit http://localhost:8000/docs for API documentation")


if __name__ == "__main__":
    asyncio.run(main())
