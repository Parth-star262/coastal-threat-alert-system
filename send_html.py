import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_CONFIG

sender_email = EMAIL_CONFIG["sender_email"]
app_password = EMAIL_CONFIG["app_password"]
receiver_email = EMAIL_CONFIG["receiver_email"]

# ==== Email content ====
subject = "HTML Email Test"

# HTML Body
html = """
<html>
  <body style="font-family: Arial; background-color:#f4f4f4; padding:20px;">
    <h2 style="color:#2E86C1;">Hello 👋,</h2>
    <p style="font-size:14px;">This is a <b>test email</b> sent using <span style="color:green;">Python + Gmail</span>.</p>
    <p>You can also add links like: 
       <a href="https://www.google.com" target="_blank">Visit Google</a>
    </p>
    <hr>
    <p style="font-size:12px; color:gray;">Regards,<br>Python Bot</p>
  </body>
</html>
"""

# ==== Setup message ====
msg = MIMEMultipart("alternative")
msg["From"] = sender_email
msg["To"] = receiver_email
msg["Subject"] = subject

msg.attach(MIMEText(html, "html"))

# ==== Send Email ====
try:
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, app_password)
    server.sendmail(sender_email, receiver_email, msg.as_string())
    server.quit()
    print("✅ HTML Email sent successfully!")
except Exception as e:
    print("❌ Error:", e)
