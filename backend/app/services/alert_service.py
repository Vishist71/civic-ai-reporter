import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.models.issue import Issue

# 🚀 CONFIGURED SENDER CREDENTIALS
SENDER_EMAIL = "chatwithharry90@gmail.com"
SENDER_PASSWORD = "aroxyihuuvighekh" 

# 🚀 EMERGENCY OFFICER EMAIL (Self-testing)
RECEIVER_EMAIL = "chatwithharry90@gmail.com" 

def send_priority_alert(issue: Issue):
    if not SENDER_EMAIL or SENDER_EMAIL == "your_email@gmail.com":
        print("Email dispatcher bypassed: Please configure sender email in alert_service.py")
        return

    subject = f"🚨 URGENT CIVIC HAZARD: #CIVIC-{issue.id} - {issue.category}"
    maps_link = f"https://www.google.com/maps?q={issue.latitude},{issue.longitude}"
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="border: 2px solid #e11d48; padding: 20px; border-radius: 10px; max-width: 600px;">
            <h2 style="color: #e11d48; margin-top: 0;">🚨 HIGH PRIORITY HAZARD DISPATCH</h2>
            <p>An automated vision-AI system has detected a high-priority civic hazard that requires immediate municipal intervention.</p>
            
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Ticket ID:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">#CIVIC-{issue.id}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Category:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd; color: #e11d48; font-weight: bold;">{issue.category}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>AI Confidence:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{int((issue.confidence or 0)*100)}%</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>SLA Deadline:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">24 Hours Standard SLA</td></tr>
            </table>
            
            <p><strong>📍 Spatial Address:</strong> {issue.address or 'Address automatically logged by GPS.'}</p>
            
            <a href="{maps_link}" style="display: inline-block; background-color: #2563eb; color: white; padding: 12px 20px; text-decoration: none; border-radius: 6px; font-weight: bold; margin-top: 10px;">
                Open GIS Location (Google Maps)
            </a>
            
            <p style="font-size: 11px; color: #6b7280; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px;">
                This is an automated dispatch from the CivicEye AI Municipal Platform. Do not reply to this email.
            </p>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['From'] = f"CivicEye AI Dispatch <{SENDER_EMAIL}>"
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            print(f"✅ EMERGENCY EMAIL SENT SUCCESSFULLY FOR #CIVIC-{issue.id}")
    except Exception as e:
        print(f"❌ ERROR SENDING EMAIL ALERT: {e}")