import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_CONFIG

# ==== Apne details yaha daalo ====
sender_email = EMAIL_CONFIG["sender_email"]
app_password = EMAIL_CONFIG["app_password"]
receiver_email = EMAIL_CONFIG["receiver_email"]

if not all((sender_email, app_password, receiver_email)):
    raise RuntimeError("Email configuration is incomplete")

# ==== Email content ====
subject = "Test Email from Python"
body = "Hello! 👋 This is a test email sent using Python + Gmail App Password."

# ==== Setup message ====
msg = MIMEMultipart()
msg["From"] = sender_email
msg["To"] = receiver_email
msg["Subject"] = subject

msg.attach(MIMEText(body, "plain"))

try:
    # Gmail SMTP server se connect
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()  # encryption ON
    server.login(sender_email, app_password)  # login with App Password
    server.sendmail(sender_email, receiver_email, msg.as_string())
    server.quit()
    print("✅ Email sent successfully!")
except Exception as e:
    print("❌ Error:", e)
