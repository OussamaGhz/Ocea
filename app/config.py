import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Database
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "pond_monitoring"
    
    # JWT
    secret_key: str = "your-secret-key-here-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # MQTT
    mqtt_broker_host: str = "broker.hivemq.com"
    mqtt_broker_port: int = 1883
    mqtt_username: str = ""
    mqtt_password: str = ""
    mqtt_topic_pattern: str = "sensors/+"
    
    # FastAPI
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # Logging
    log_level: str = "INFO"
    
    # Twilio SMS
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    alert_phone_number: str = ""
    
    # Sensor Thresholds
    ph_min: float = 6.5
    ph_max: float = 8.5
    temperature_min: float = 20.0
    temperature_max: float = 30.0
    dissolved_oxygen_min: float = 5.0
    dissolved_oxygen_max: float = 15.0
    turbidity_max: float = 10.0
    nitrate_max: float = 40.0
    nitrite_max: float = 0.5
    ammonia_max: float = 0.5
    water_level_min: float = 0.5
    water_level_max: float = 3.0
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
