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
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
