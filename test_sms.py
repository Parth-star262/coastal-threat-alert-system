from alerts import send_sms_alert
from config import TWILIO_CONFIG

# Twilio credentials
account_sid = TWILIO_CONFIG["account_sid"]
auth_token = TWILIO_CONFIG["auth_token"]
from_number = TWILIO_CONFIG["from_number"]
to_number = TWILIO_CONFIG["to_number"]

if not all((account_sid, auth_token, from_number, to_number)):
    raise RuntimeError("Twilio configuration is incomplete")

# Test SMS
send_sms_alert(
    account_sid,
    auth_token,
    from_number,
    to_number,
    city="Mumbai",
    description="Cyclone Warning 🌪️"
)
