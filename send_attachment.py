import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from config import EMAIL_CONFIG

sender_email = EMAIL_CONFIG["sender_email"]
app_password = EMAIL_CONFIG["app_password"]
receiver_email = EMAIL_CONFIG["receiver_email"]

# ==== Email content ====
subject = "Test Email with Attachment"
body = "Hello 👋,\n\nThis email has an attachment.\n\nRegards,\nPython Bot"

# ==== Setup message ====
msg = MIMEMultipart()
msg["From"] = sender_email
msg["To"] = receiver_email
msg["Subject"] = subject

msg.attach(MIMEText(body, "plain"))

# ==== File attach karna ====
filename = "problem statements (1).pdf"   # jis file ko attach karna hai (same folder me ho)
try:
    with open(filename, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    # Encode file
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f"attachment; filename={filename}",
    )
    msg.attach(part)
except Exception as e:
    print("⚠️ File error:", e)

# ==== Send Email ====
try:
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, app_password)
    server.sendmail(sender_email, receiver_email, msg.as_string())
    server.quit()
    print("✅ Email with attachment sent successfully!")
except Exception as e:
    print("❌ Error:", e)
