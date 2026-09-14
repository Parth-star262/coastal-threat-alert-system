import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client

# -----------------------------
# EMAIL ALERT FUNCTION
# -----------------------------
def send_email_alert(sender_email, app_password, receiver_email, city, temperature, humidity, wind_speed, description):
    try:
        subject = f"⚠️ ALERT: Severe Weather in {city}"
        body = f"""
        Coastal Threat Alert 🚨

        City: {city}
        Temperature: {temperature}°C
        Humidity: {humidity}%
        Wind Speed: {wind_speed} m/s
        Condition: {description}

        Please take precautionary measures.
        """

        # setup mail
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Gmail SMTP server
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()

        print("✅ Email Alert Sent Successfully!")
        return True
    except Exception as e:
        print("❌ Email Error:", e)
        return False


# -----------------------------
# SMS ALERT FUNCTION (Twilio)
# -----------------------------
def send_sms_alert(account_sid, auth_token, from_number, to_number, city, description):
    try:
        client = Client(account_sid, auth_token)

        message_body = f"⚠️ Coastal Threat Alert 🚨\nCity: {city}\nCondition: {description}\nStay Safe!"

        message = client.messages.create(
            body=message_body,
            from_=from_number,   # Twilio number
            to=to_number         # Verified user number
        )

        print("✅ SMS Alert Sent Successfully! SID:", message.sid)
        return True
    except Exception as e:
        print("❌ SMS Error:", e)
        return False
