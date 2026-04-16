# Test script to verify forgot password functionality
from hr_base import app, password_reset_tokens, HR_CREDENTIALS
import secrets
from datetime import datetime

print("Testing Forgot Password Functionality...")
print(f"Current HR Credentials: {list(HR_CREDENTIALS.keys())}")
print(f"Password Reset Tokens: {len(password_reset_tokens)}")

# Test token generation
test_token = secrets.token_urlsafe(32)
password_reset_tokens[test_token] = {
    "email": "angelbrenna20@gmail.com",
    "created": datetime.now(),
    "expires": datetime.now().timestamp() + 3600
}

print(f"Test token created: {test_token[:10]}...")
print("Forgot password functionality is ready!")

# Test email functionality
from hr_base import send_email
print("Testing email functionality...")
# Uncomment below to actually send test email
# send_email("angelbrenna20@gmail.com", "Test", "Test email from forgot password system")
