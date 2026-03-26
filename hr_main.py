"""
Main HR Portal Application - Consolidates all HR modules
This is the main entry point that imports and combines all HR functionality
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from database import ResumeDatabase
import os

# Import all HR modules
from hr_base import app, get_current_user, get_base_html, get_end_html, send_email
from hr_dashboard_page import *
from hr_jobs import *
from hr_interviews import *
from hr_communications import *
from hr_offers import *
from hr_reports import *
from hr_post_job import *

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
    print("  • Post Job: http://localhost:8003/post-job")
    print("================================")
    print("Demo Credentials:")
    print("  Email: angelbrenna20@gmail.com")
    print("  Password: Niyigena2003@")
    print("================================")
    
    uvicorn.run(app, host="0.0.0.0", port=8003)
