import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
from config import EMAIL_CONFIG, TWILIO_CONFIG, ALERT_THRESHOLDS
from config import DB_CONFIG, NOTIFICATION_MAX_RETRIES, NOTIFICATION_TEST_MODE
import psycopg2
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertService:
    def __init__(self):
        self.email_config = EMAIL_CONFIG
        self.twilio_config = TWILIO_CONFIG
    
    def send_email_alert(self, city, temperature, humidity, wind_speed, description):
        """Send email alert for severe weather conditions"""
        try:
            subject = f"⚠️ ALERT: Severe Weather in {city}"
            body = f"""
            🌊 Coastal Threat Alert ��

            City: {city}
            Temperature: {temperature}°C
            Humidity: {humidity}%
            Wind Speed: {wind_speed} m/s
            Condition: {description}

            Please take precautionary measures.
            """
            
            msg = MIMEMultipart()
            msg["From"] = self.email_config['sender_email']
            msg["To"] = self.email_config['receiver_email']
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.email_config['sender_email'], self.email_config['app_password'])
            server.sendmail(self.email_config['sender_email'], self.email_config['receiver_email'], msg.as_string())
            server.quit()
            
            logger.info(f"✅ Email Alert Sent for {city}!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Email failed for {city}: {e}")
            return False
    
    def send_sms_alert(self, city, description):
        """Send SMS alert using Twilio"""
        try:
            client = Client(self.twilio_config['account_sid'], self.twilio_config['auth_token'])
            
            message_body = f"⚠️ Coastal Threat Alert 🚨\nCity: {city}\nCondition: {description}\nStay Safe!"
            
            message = client.messages.create(
                body=message_body,
                from_=self.twilio_config['from_number'],
                to=self.twilio_config['to_number']
            )
            
            logger.info(f"✅ SMS Alert Sent for {city}! SID: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"❌ SMS failed for {city}: {e}")
            return False
    
    def should_send_alert(self, wind_speed, humidity):
        """Check if alert conditions are met"""
        return (wind_speed > ALERT_THRESHOLDS['wind_speed_medium'] or 
                humidity > ALERT_THRESHOLDS['humidity_medium'])

    def create_weather_alert(self, city, temperature, humidity, wind_speed, description, observed_at=None):
        if wind_speed >= ALERT_THRESHOLDS['wind_speed_high'] or humidity >= ALERT_THRESHOLDS['humidity_high']:
            severity = "CRITICAL"
            action = "Move away from exposed coastal areas and follow emergency instructions."
        elif self.should_send_alert(wind_speed, humidity):
            severity = "HIGH"
            action = "Monitor official warnings and prepare precautionary measures."
        else:
            return None

        trigger = f"wind={wind_speed};humidity={humidity}"
        dedupe_key = f"weather:{city}:{severity}:{str(observed_at or '')}"
        message = f"Weather alert in {city}: {description}"
        with psycopg2.connect(**DB_CONFIG) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO alerts
                        (dedupe_key, city, severity, confidence, trigger, message,
                         recommended_action, observed_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (dedupe_key) DO NOTHING
                    RETURNING id, status
                    """,
                    (dedupe_key, city, severity, None, trigger, message, action, observed_at),
                )
                return cursor.fetchone()

    def notify_alert(self, alert_id, city, temperature, humidity, wind_speed, description):
        if NOTIFICATION_TEST_MODE:
            results = {"email": True, "sms": True}
        else:
            results = {
                "email": self._retry(
                    self.send_email_alert, city, temperature, humidity, wind_speed, description
                ),
                "sms": self._retry(self.send_sms_alert, city, description),
            }
        recipients = {
            "email": self.email_config.get("receiver_email"),
            "sms": self.twilio_config.get("to_number"),
        }
        with psycopg2.connect(**DB_CONFIG) as connection:
            with connection.cursor() as cursor:
                for channel, successful in results.items():
                    cursor.execute(
                        """
                        INSERT INTO notifications
                            (alert_id, channel, recipient, status, error_message, sent_at)
                        VALUES (%s, %s, %s, %s, %s, CASE WHEN %s THEN NOW() ELSE NULL END)
                        ON CONFLICT (alert_id, channel) DO UPDATE SET
                            status = EXCLUDED.status,
                            error_message = EXCLUDED.error_message,
                            sent_at = EXCLUDED.sent_at
                        """,
                        (
                            alert_id,
                            channel,
                            recipients[channel],
                            "test" if NOTIFICATION_TEST_MODE else ("sent" if successful else "failed"),
                            None if successful else "Notification provider rejected or was unavailable",
                            successful,
                        ),
                    )
        return results

    @staticmethod
    def _retry(function, *args):
        for _ in range(NOTIFICATION_MAX_RETRIES):
            if function(*args):
                return True
        return False