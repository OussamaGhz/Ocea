#!/usr/bin/env python3
"""
Pond Monitoring Status

This script provides a real-time status view of all active ponds and their sensor data.

Usage:
    python pond_status.py
"""

import asyncio
import time
from datetime import datetime, timedelta
import pymongo
from app.config import get_settings

settings = get_settings()


class PondMonitor:
    def __init__(self):
        self.client = pymongo.MongoClient(settings.mongodb_url)
        self.db = self.client[settings.database_name]
        self.collection = self.db.sensor_readings
    
    def get_pond_status(self):
        """Get current status of all ponds"""
        try:
            # Get recent data for each pond (last 5 minutes)
            five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
            
            pipeline = [
                {
                    "$match": {
                        "timestamp": {"$gte": five_minutes_ago}
                    }
                },
                {
                    "$group": {
                        "_id": "$pond_id",
                        "count": {"$sum": 1},
                        "latest_reading": {"$max": "$timestamp"},
                        "latest_ph": {"$last": "$ph"},
                        "latest_temp": {"$last": "$temperature"},
                        "latest_do": {"$last": "$dissolved_oxygen"},
                        "latest_turbidity": {"$last": "$turbidity"},
                        "latest_nitrate": {"$last": "$nitrate"},
                        "latest_nitrite": {"$last": "$nitrite"},
                        "latest_ammonia": {"$last": "$ammonia"},
                        "latest_water_level": {"$last": "$water_level"}
                    }
                },
                {
                    "$sort": {"_id": 1}
                }
            ]
            
            results = list(self.collection.aggregate(pipeline))
            return results
            
        except Exception as e:
            print(f"Error fetching pond status: {e}")
            return []
    
    def get_total_readings(self):
        """Get total count of all sensor readings"""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$pond_id",
                        "total_count": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"_id": 1}
                }
            ]
            
            results = list(self.collection.aggregate(pipeline))
            return results
            
        except Exception as e:
            print(f"Error fetching total readings: {e}")
            return []
    
    def display_status(self):
        """Display current pond status"""
        print("\n" + "="*80)
        print("🏊 POND MONITORING SYSTEM STATUS")
        print("="*80)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Get active ponds (last 5 minutes)
        active_ponds = self.get_pond_status()
        
        if not active_ponds:
            print("\n❌ No active ponds found (no data in last 5 minutes)")
            return
        
        print(f"\n🟢 ACTIVE PONDS ({len(active_ponds)} ponds with recent data)")
        print("-" * 80)
        
        for pond in active_ponds:
            pond_id = pond['_id']
            count = pond['count']
            latest = pond['latest_reading']
            age = datetime.utcnow() - latest
            age_seconds = int(age.total_seconds())
            
            print(f"\n📊 {pond_id}")
            print(f"   📈 Recent readings: {count} (last {age_seconds}s ago)")
            print(f"   🧪 pH: {pond['latest_ph']:.2f}")
            print(f"   🌡️  Temperature: {pond['latest_temp']:.2f}°C")
            print(f"   💨 Dissolved Oxygen: {pond['latest_do']:.2f} mg/L")
            print(f"   🌊 Turbidity: {pond['latest_turbidity']:.2f} NTU")
            print(f"   🔴 Nitrate: {pond['latest_nitrate']:.2f} mg/L")
            print(f"   🔵 Nitrite: {pond['latest_nitrite']:.3f} mg/L")
            print(f"   🟡 Ammonia: {pond['latest_ammonia']:.3f} mg/L")
            print(f"   📏 Water Level: {pond['latest_water_level']:.2f} m")
        
        # Get total readings
        total_readings = self.get_total_readings()
        print(f"\n📈 TOTAL READINGS BY POND")
        print("-" * 40)
        for pond in total_readings:
            pond_id = pond['_id']
            total = pond['total_count']
            print(f"   {pond_id}: {total} readings")
        
        print("\n" + "="*80)
    
    def run_continuous(self, interval=10):
        """Run continuous monitoring"""
        print("🚀 Starting continuous pond monitoring...")
        print(f"📡 Refreshing every {interval} seconds")
        print("🛑 Press Ctrl+C to stop")
        
        try:
            while True:
                self.display_status()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Error in monitoring: {e}")
    
    def run_once(self):
        """Run one-time status check"""
        self.display_status()
        print("\n✅ Status check complete")


def main():
    monitor = PondMonitor()
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        monitor.run_continuous()
    else:
        monitor.run_once()


if __name__ == "__main__":
    main()
