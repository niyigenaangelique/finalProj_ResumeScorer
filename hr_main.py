"""
Main HR Portal Application - Consolidates all HR modules
This is the main entry point that imports and combines all HR functionality
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from database import ResumeDatabase
import os
import sqlite3

# Import all HR modules
from hr_base import app, get_current_user, get_base_html, get_end_html, send_email
from hr_dashboard_page import *
from hr_jobs import *
from hr_interviews import *
from hr_communications import *
from hr_offers import *
from hr_reports import *
from hr_post_job import *
from hr_evaluation import *

# Contact Messages API Endpoints
@app.post("/api/contact-message")
async def submit_contact_message(request: Request):
    """Submit a contact message from the contact form"""
    try:
        data = await request.json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'subject', 'message']
        for field in required_fields:
            if field not in data or not data[field].strip():
                return JSONResponse(
                    content={"error": f"Field '{field}' is required"}, 
                    status_code=400
                )
        
        # Save the message
        success = db.save_contact_message(
            name=data['name'].strip(),
            email=data['email'].strip(),
            subject=data['subject'].strip(),
            message=data['message'].strip()
        )
        
        if success:
            return JSONResponse(content={
                "success": True, 
                "message": "Your message has been sent successfully!"
            })
        else:
            return JSONResponse(
                content={"error": "Failed to save message"}, 
                status_code=500
            )
            
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/api/contact-messages")
async def get_contact_messages():
    """Get all contact messages"""
    try:
        messages = db.get_contact_messages()
        return JSONResponse(content=messages)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/api/contact-messages/unread")
async def get_unread_contact_messages():
    """Get unread contact messages"""
    try:
        messages = db.get_contact_messages(status='unread')
        return JSONResponse(content=messages)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.put("/api/contact-messages/{message_id}/mark-read")
async def mark_contact_message_read(message_id: int):
    """Mark a contact message as read"""
    try:
        success = db.mark_contact_message_read(message_id)
        if success:
            return JSONResponse(content={
                "success": True, 
                "message": "Message marked as read"
            })
        else:
            return JSONResponse(
                content={"error": "Message not found"}, 
                status_code=404
            )
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/api/contact-unread-count")
async def get_unread_contact_count():
    """Get count of unread contact messages"""
    try:
        count = db.get_unread_contact_count()
        return JSONResponse(content={"count": count})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# Initialize database
db = ResumeDatabase()

# Add any additional shared endpoints or middleware
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "HR Portal", "version": "1.0.0"}

@app.get("/api/stats")
async def get_dashboard_stats(request: Request):
    """Get dashboard statistics for API calls"""
    current_user = get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        statistics = db.get_statistics()
        applications = db.get_all_applications()
        
        return {
            "success": True,
            "statistics": statistics,
            "recent_applications": applications[:5]  # Last 5 applications
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# Add error handling
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    current_user = get_current_user(request)
    if current_user:
        # User is logged in, show custom 404 page
        return HTMLResponse(content=f"""
            {get_base_html("Page Not Found", "", current_user)}
            <div class="card">
                <h2>Page Not Found</h2>
                <p>The page you're looking for doesn't exist.</p>
                <div style="margin-top: 1rem;">
                    <a href="/dashboard" class="btn btn-primary">Go to Dashboard</a>
                </div>
            </div>
            {get_end_html()}
        """, status_code=404)
    else:
        # User not logged in, redirect to login
        return RedirectResponse(url="/", status_code=302)

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors"""
    current_user = get_current_user(request)
    if current_user:
        return HTMLResponse(content=f"""
            {get_base_html("Server Error", "", current_user)}
            <div class="card">
                <h2>Server Error</h2>
                <p>Something went wrong on our end. Please try again later.</p>
                <div style="margin-top: 1rem;">
                    <a href="/dashboard" class="btn btn-primary">Go to Dashboard</a>
                </div>
            </div>
            {get_end_html()}
        """, status_code=500)
    else:
        return RedirectResponse(url="/", status_code=302)

if __name__ == "__main__":
    import uvicorn
    print("Starting ZIBITECH HR Portal...")
    print("================================")
    print("Available Pages:")
    print("  • Login: http://localhost:8003/")
    print("  • Dashboard: http://localhost:8003/dashboard")
    print("  • Job Management: http://localhost:8003/jobs")
    print("  • Interview Scheduling: http://localhost:8003/interviews")
    print("  • Communications: http://localhost:8003/communications")
    print("  • Offer Management: http://localhost:8003/offers")
    print("  • Reports: http://localhost:8003/reports")
    print("  • Evaluations: http://localhost:8003/evaluations")
    print("  • Post Job: http://localhost:8003/post-job")
    print("================================")
    print("Demo Credentials:")
    print("  Email: angelbrenna20@gmail.com")
    print("  Password: Niyigena2003@")
    print("================================")
    
    uvicorn.run(app, host="0.0.0.0", port=8003)
    