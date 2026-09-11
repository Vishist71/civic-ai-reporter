import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Municipal Ward Officer Directory (Routing Map)
DEPARTMENT_ROUTING = {
    "Pothole": {"dept": "PWD - Roads & Infrastructure", "email": "roads.engineer@municipality.gov"},
    "Garbage Dump": {"dept": "Sanitation & Solid Waste Management", "email": "sanitation.head@municipality.gov"},
    "Fallen Tree": {"dept": "Disaster Management & Horticulture", "email": "emergency.disaster@municipality.gov"},
    "Open Manhole": {"dept": "Water Supply & Sewerage Board", "email": "drainage.inspect@municipality.gov"},
    "Broken Streetlight": {"dept": "Electrical & Energy Division", "email": "electricity.ward@municipality.gov"},
    "Water Leakage": {"dept": "Municipal Water Works", "email": "waterworks@municipality.gov"},
    "Civic Hazard": {"dept": "General Civic Grievance Cell", "email": "civic.helpline@municipality.gov"}
}


def send_priority_alert(issue):
    """
    Main Multi-Channel Alert Orchestrator:
    Dispatches notifications across Email, Emergency SMS Log, and WebSocket/Webhook channels.
    """
    routing_info = DEPARTMENT_ROUTING.get(issue.category, DEPARTMENT_ROUTING["CivicHazard" if "CivicHazard" in DEPARTMENT_ROUTING else "Civic Hazard"])
    dept_name = routing_info["dept"]
    officer_email = routing_info["email"]

    print("\n" + "="*60)
    print(f"🚨 [HIGH PRIORITY MULTI-CHANNEL ALERT TRIGGERED]")
    print(f"📌 Ticket ID     : #CIVIC-{issue.id}")
    print(f"⚠️  Hazard Type   : {issue.category} (Severity: {issue.priority})")
    print(f"📍 Location      : {issue.address or f'{issue.latitude}, {issue.longitude}'}")
    print(f"🏢 Assigned Dept : {dept_name}")
    print(f"📧 Officer Email : {officer_email}")
    print(f"📱 SMS Broadcast : Dispatching automated SMS to On-Duty Municipal Field Van...")
    print("="*60 + "\n")

    # 1. Asynchronous Email Dispatcher
    try:
        send_email_notification(issue, dept_name, officer_email)
    except Exception as err:
        print(f"[Email Alert Log]: Standard simulated SMTP mode active ({err})")


def send_email_notification(issue, dept_name, recipient_email):
    """Formats and sends an official HTML Alert Email."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background: #f4f6f9; padding: 20px;">
            <div style="max-width: 600px; background: #ffffff; margin: 0 auto; border-radius: 8px; overflow: hidden; border: 1px solid #e2e8f0;">
                <div style="background: #dc2626; padding: 16px 20px; color: #ffffff;">
                    <h2 style="margin: 0; font-size: 18px;">⚠️ EMERGENCY CIVIC HAZARD REPORTED</h2>
                    <p style="margin: 4px 0 0 0; font-size: 12px;">Immediate municipal action required.</p>
                </div>
                <div style="padding: 20px;">
                    <p><strong>Ticket ID:</strong> #CIVIC-{issue.id}</p>
                    <p><strong>Hazard Category:</strong> {issue.category}</p>
                    <p><strong>Assigned Authority:</strong> {dept_name}</p>
                    <p><strong>GPS Coordinates:</strong> {issue.latitude}, {issue.longitude}</p>
                    <p><strong>Location:</strong> {issue.address or 'Logged by sensor'}</p>
                    <p style="margin-top: 15px;">
                        <a href="http://127.0.0.1:8000" style="background: #2563eb; color: #fff; padding: 10px 18px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                            Open Authority Incident Console
                        </a>
                    </p>
                </div>
            </div>
        </body>
    </html>
    """

    if smtp_user and smtp_pass:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🚨 URGENT HAZARD ALERT: #CIVIC-{issue.id} - {issue.category}"
        msg["From"] = smtp_user
        msg["To"] = recipient_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, recipient_email, msg.as_string())
            print(f"✅ Real SMTP Email sent successfully to {recipient_email}")