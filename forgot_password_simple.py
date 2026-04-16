# Simple Forgot Password Implementation
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from hr_base import app, password_reset_tokens, HR_CREDENTIALS, send_email
from datetime import datetime
import secrets
from jinja2 import Template

# Simple Forgot Password Page
@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page():
    """Display forgot password page"""
    html = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Forgot Password - TalentFlow HR</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f5f5f5; padding: 50px; }
        .container { max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h2 { color: #333; text-align: center; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; color: #555; }
        input[type="email"] { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 16px; }
        button { width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .back-link { display: block; text-align: center; margin-top: 20px; color: #666; text-decoration: none; }
        .error { color: #dc3545; background: #f8d7da; padding: 10px; border-radius: 4px; margin-bottom: 20px; }
        .success { color: #155724; background: #d4edda; padding: 10px; border-radius: 4px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>TalentFlow HR - Forgot Password</h2>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        {% if success %}
        <div class="success">{{ success }}</div>
        {% endif %}
        
        <form method="post">
            <div class="form-group">
                <label for="email">Email Address:</label>
                <input type="email" id="email" name="email" required placeholder="Enter your HR email">
            </div>
            <button type="submit">Send Reset Link</button>
        </form>
        
        <a href="/" class="back-link">Back to Login</a>
    </div>
</body>
</html>
    '''
    return HTMLResponse(content=Template(html).render(error=None, success=None))

@app.post("/forgot-password")
async def forgot_password_submit(request: Request):
    """Handle forgot password form submission"""
    form = await request.form()
    email = form.get("email", "").strip()
    
    if not email:
        html = '''
<!DOCTYPE html>
<html>
<head><title>Forgot Password - TalentFlow HR</title></head>
<body>
    <div class="container">
        <h2>TalentFlow HR - Forgot Password</h2>
        <div class="error">Email is required</div>
        <a href="/forgot-password">Back</a>
    </div>
</body>
</html>
        '''
        return HTMLResponse(content=html, status_code=400)
    
    # Check if email exists
    if email not in HR_CREDENTIALS:
        html = '''
<!DOCTYPE html>
<html>
<head><title>Forgot Password - TalentFlow HR</title></head>
<body>
    <div class="container">
        <h2>TalentFlow HR - Forgot Password</h2>
        <div class="success">If an account with that email exists, a password reset link has been sent.</div>
        <a href="/">Back to Login</a>
    </div>
</body>
</html>
        '''
        return HTMLResponse(content=html)
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    password_reset_tokens[reset_token] = {
        "email": email,
        "created": datetime.now(),
        "expires": datetime.now().timestamp() + 3600
    }
    
    # Create reset link
    reset_link = "http://localhost:8003/reset-password?token=" + reset_token
    
    # Send email
    subject = "Password Reset - TalentFlow HR Portal"
    body = "Hello " + email + ",\\n\\nYou requested to reset your password. Click this link:\\n" + reset_link + "\\n\\nThis link expires in 1 hour.\\n\\nTalentFlow HR Team"
    
    try:
        send_email(email, subject, body, is_html=False)
        html = '''
<!DOCTYPE html>
<html>
<head><title>Forgot Password - TalentFlow HR</title></head>
<body>
    <div class="container">
        <h2>TalentFlow HR - Forgot Password</h2>
        <div class="success">Password reset link has been sent to your email.</div>
        <a href="/">Back to Login</a>
    </div>
</body>
</html>
        '''
        return HTMLResponse(content=html)
    except:
        html = '''
<!DOCTYPE html>
<html>
<head><title>Forgot Password - TalentFlow HR</title></head>
<body>
    <div class="container">
        <h2>TalentFlow HR - Forgot Password</h2>
        <div class="error">Failed to send email. Please try again.</div>
        <a href="/forgot-password">Back</a>
    </div>
</body>
</html>
        '''
        return HTMLResponse(content=html, status_code=500)

print("Forgot password functionality loaded successfully!")
print("Available endpoints:")
print("- GET /forgot-password - Display forgot password form")
print("- POST /forgot-password - Submit forgot password form")
print("HR Credentials:", list(HR_CREDENTIALS.keys()))
