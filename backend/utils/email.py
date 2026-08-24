import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings
import logging

logger = logging.getLogger(__name__)

async def send_email(to_email: str, subject: str, body: str, is_html: bool = True):
    """Send email to user"""
    try:
        message = MIMEMultipart()
        message["From"] = settings.SENDER_EMAIL
        message["To"] = to_email
        message["Subject"] = subject
        
        message.attach(MIMEText(body, "html" if is_html else "plain"))
        
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SENDER_EMAIL, settings.SENDER_PASSWORD)
            server.send_message(message)
        
        logger.info(f"Email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False

async def send_complaint_status_email(email: str, complaint_id: str, status: str, note: str = ""):
    """Send email when complaint status changes"""
    subject = f"Complaint #{complaint_id} Status Updated"
    body = f"""
    <html>
        <body>
            <h2>Complaint Status Update</h2>
            <p>Your complaint <strong>#{complaint_id}</strong> has been updated.</p>
            <p><strong>New Status:</strong> {status.replace('_', ' ').title()}</p>
            {f'<p><strong>Note:</strong> {note}</p>' if note else ''}
            <p>Please log in to view more details.</p>
        </body>
    </html>
    """
    return await send_email(email, subject, body)

async def send_important_notice_email(email: str, notice_title: str):
    """Send email when important notice is posted"""
    subject = f"Important Notice: {notice_title}"
    body = f"""
    <html>
        <body>
            <h2>New Important Notice</h2>
            <p>A new important notice has been posted on the notice board.</p>
            <p><strong>Title:</strong> {notice_title}</p>
            <p>Please log in to view the full notice.</p>
        </body>
    </html>
    """
    return await send_email(email, subject, body)
