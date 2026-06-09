import os
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from app.core.config import settings
from pydantic import EmailStr
from typing import List, Dict, Any

conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_EMAIL,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.SMTP_EMAIL,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    # TEMPLATE_FOLDER=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
)

fast_mail = FastMail(conf)

async def send_email(subject: str, recipients: List[EmailStr], body: str):
    """
    Asynchronously send an email using fastapi-mail.
    """
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=body,
        subtype=MessageType.html
    )
    
    await fast_mail.send_message(message)
