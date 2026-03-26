import requests
import json

def test_email_setup():
    """Test email sending functionality and show setup instructions"""
    session = requests.Session()
    
    # Login
    login_data = {'email': 'angelbrenna20@gmail.com', 'password': 'Niyigena2003@'}
    response = session.post('http://localhost:8003/login', data=login_data, allow_redirects=False)
    
    if response.status_code != 302:
        print('❌ Login failed')
        return False
    
    print('✅ Login successful')
    
    # Test sending an email
    email_data = {
        'application_id': '1',
        'recipient_email': 'angelbrenna20@gmail.com',
        'subject': 'Test Email from HR Portal',
        'message_type': 'update',
        'email_body': '<h2>Test Email</h2><p>This is a test email from the HR portal.</p>',
        'send_copy': False
    }
    
    send_response = session.post('http://localhost:8003/api/send-communication', json=email_data)
    print(f'Send email API status: {send_response.status_code}')
    
    if send_response.status_code == 200:
        result = send_response.json()
        if result.get('success'):
            print('✅ Email sent successfully!')
            return True
        else:
            print(f'❌ Email failed: {result.get("error")}')
            
            # Check if it's the Gmail App Password issue
            if "App Password" in result.get("error", ""):
                print("\n🔧 EMAIL SETUP INSTRUCTIONS:")
                print("=" * 50)
                print("1. Go to: https://myaccount.google.com/apppasswords")
                print("2. Sign in with your Google account")
                print("3. Select 'Mail' for the app")
                print("4. Click 'Generate'")
                print("5. Copy the 16-character password (without spaces)")
                print("6. Update EMAIL_PASSWORD in hr_base.py line 24")
                print("7. Restart the server")
                print("=" * 50)
            
            return False
    else:
        print(f'❌ Send email API failed: {send_response.status_code}')
        print(f'Response: {send_response.text[:200]}')
        return False

if __name__ == "__main__":
    print("🔍 Testing Email Setup & Configuration")
    print("=" * 50)
    
    success = test_email_setup()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Email functionality is WORKING!")
    else:
        print("❌ Email functionality needs setup")
        print("\n📧 QUICK FIX:")
        print("1. Enable 2-Factor Authentication on your Google account")
        print("2. Generate an App Password: https://myaccount.google.com/apppasswords")
        print("3. Update EMAIL_PASSWORD in hr_base.py")
        print("4. Restart the server")
