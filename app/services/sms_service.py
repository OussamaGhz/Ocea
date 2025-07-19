"""
Twilio SMS Service for Alert Notifications
"""
import logging
from typing import Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TwilioSMSService:
    def __init__(self):
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Twilio client if credentials are provided"""
        if settings.twilio_account_sid and settings.twilio_auth_token:
            try:
                self.client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
                logger.info("Twilio SMS service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.client = None
        else:
            logger.warning("Twilio credentials not provided. SMS service disabled.")

    def is_enabled(self) -> bool:
        """Check if SMS service is properly configured"""
        return (self.client is not None and 
                settings.twilio_phone_number and 
                settings.alert_phone_number)

    async def send_alert_sms(self, message: str, pond_id: str, alert_type: str) -> bool:
        """Send SMS alert for pond monitoring"""
        if not self.is_enabled():
            logger.warning("SMS service not enabled. Skipping SMS alert.")
            return False

        try:
            # Format the message with pond info
            formatted_message = f"🚨 POND ALERT\n\nPond: {pond_id}\nAlert: {alert_type}\n\n{message}\n\nTime: {logger.time.strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Send SMS
            message_obj = self.client.messages.create(
                body=formatted_message,
                from_=settings.twilio_phone_number,
                to=settings.alert_phone_number
            )
            
            logger.info(f"SMS alert sent successfully. SID: {message_obj.sid}")
            return True

        except TwilioException as e:
            logger.error(f"Twilio error sending SMS: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending SMS: {e}")
            return False

    async def send_critical_alert(self, pond_id: str, parameter: str, value: float, threshold: float) -> bool:
        """Send critical alert SMS"""
        message = f"CRITICAL: {parameter.upper()} level is {value} (threshold: {threshold}). Immediate attention required!"
        return await self.send_alert_sms(message, pond_id, f"{parameter}_critical")

    async def send_high_alert(self, pond_id: str, parameter: str, value: float, threshold: float) -> bool:
        """Send high severity alert SMS"""
        message = f"HIGH: {parameter.upper()} level is {value} (threshold: {threshold}). Please check soon."
        return await self.send_alert_sms(message, pond_id, f"{parameter}_high")

    async def test_sms(self) -> bool:
        """Send test SMS to verify configuration"""
        if not self.is_enabled():
            return False

        try:
            test_message = "🧪 Test message from Pond Monitoring System. SMS notifications are working correctly!"
            
            message_obj = self.client.messages.create(
                body=test_message,
                from_=settings.twilio_phone_number,
                to=settings.alert_phone_number
            )
            
            logger.info(f"Test SMS sent successfully. SID: {message_obj.sid}")
            return True

        except Exception as e:
            logger.error(f"Test SMS failed: {e}")
            return False


# Global SMS service instance
sms_service = TwilioSMSService()
