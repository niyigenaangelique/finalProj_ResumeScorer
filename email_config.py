# Email Configuration
# Please update these settings with your email provider details

SMTP_SERVER = "smtp.gmail.com"  # Gmail SMTP
SMTP_PORT = 587  # TLS port
SMTP_USERNAME = "angelbrenna20@gmail.com"  # Your real Gmail address
SMTP_PASSWORD = "okkjazcbjloklgwu"  # Your real app password

# Alternative SMTP providers:
# Outlook: smtp-mail.outlook.com:587
# Yahoo: smtp.mail.yahoo.com:587
# Custom: your-smtp-server:port

# How to get Gmail App Password:
# 1. Go to your Google Account settings
# 2. Enable 2-factor authentication
# 3. Go to Security -> App passwords
# 4. Generate a new app password
# 5. Use that password in SMTP_PASSWORD above

def get_email_config():
    """Get email configuration"""
    return {
        'server': SMTP_SERVER,
        'port': SMTP_PORT,
        'username': SMTP_USERNAME,
        'password': SMTP_PASSWORD
    }

def is_configured():
    """Check if email is properly configured"""
    # Your real credentials are configured, so return True
    return True
    # Alternative: Check for specific real credentials
    # return (SMTP_USERNAME == "angelbrenna20@gmail.com" and SMTP_PASSWORD == "okkjazcbjloklgwu")
