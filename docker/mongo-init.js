// MongoDB initialization script
db = db.getSiblingDB('pond_monitoring');

// Create collections with validation
db.createCollection('users', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['username', 'email', 'hashed_password'],
      properties: {
        username: { bsonType: 'string', minLength: 3, maxLength: 50 },
        email: { bsonType: 'string', pattern: '^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$' },
        hashed_password: { bsonType: 'string' },
        is_active: { bsonType: 'bool' },
        is_admin: { bsonType: 'bool' }
      }
    }
  }
});

db.createCollection('farms');
db.createCollection('ponds');
db.createCollection('sensor_readings');
db.createCollection('alerts');
db.createCollection('system_logs');

// Create indexes
db.users.createIndex({ username: 1 }, { unique: true });
db.users.createIndex({ email: 1 }, { unique: true });
db.farms.createIndex({ owner_id: 1 });
db.ponds.createIndex({ pond_id: 1 }, { unique: true });
db.ponds.createIndex({ farm_id: 1 });
db.sensor_readings.createIndex({ pond_id: 1, timestamp: -1 });
db.sensor_readings.createIndex({ timestamp: 1 });
db.sensor_readings.createIndex({ is_anomaly: 1 });
db.alerts.createIndex({ pond_id: 1, created_at: -1 });
db.alerts.createIndex({ is_acknowledged: 1 });

print('Database initialized successfully!');
