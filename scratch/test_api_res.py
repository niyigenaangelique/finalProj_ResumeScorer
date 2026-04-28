import requests
import json

url = "http://localhost:8003/api/generate-report"
data = {
    "report_type": "applications",
    "report_format": "html",
    "include_charts": "on",
    "start_date": "2020-01-01",
    "end_date": "2030-01-01",
    "department_filter": ""
}

# Need to login first or mock auth?
# The API uses get_current_user(request) which checks 'hr_token' cookie.
# I'll try to find a valid token or bypass auth if I can.
# Actually, I'll just check the code to see if I can bypass it for testing.
print("Testing API locally...")
# I'll just run the function directly instead of making a real HTTP request to avoid auth issues.
from hr_reports import _generate_report_data
res = _generate_report_data("applications", data)
print(f"Success: {'charts' in res}")
if 'charts' in res:
    print(f"Charts: {list(res['charts'].keys())}")
else:
    print("No charts in response!")
