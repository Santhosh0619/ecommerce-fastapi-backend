def generate_email_html(title: str, message: str) -> str:
    """Generate a simple, reusable HTML wrapper for emails."""
    # Convert newlines in message to <br> tags for HTML
    formatted_message = message.replace('\n', '<br/>')
    
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
            <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">{title}</h2>
            <div style="padding: 15px 0;">
                {formatted_message}
            </div>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;"/>
            <p style="font-size: 12px; color: #999; text-align: center;">
                This is an automated notification from your E-Commerce Platform.<br/>
                Please do not reply directly to this email.
            </p>
        </div>
    </body>
    </html>
    """
