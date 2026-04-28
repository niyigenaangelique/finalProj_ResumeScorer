from hr_reports import _generate_report_data
import json

# Mock params
params = {
    'report_type': 'applications',
    'report_format': 'html',
    'include_charts': 'on',
    'department_filter': '',
    'start_date': '2020-01-01',
    'end_date': '2030-01-01'
}

print("Generating report data with charts...")
try:
    data = _generate_report_data('applications', params)
    print(f"Success! Total applications: {data.get('total_applications')}")
    
    charts = data.get('charts', {})
    if charts:
        print(f"Charts generated: {list(charts.keys())}")
        for name, b64 in charts.items():
            print(f"  - {name}: {len(b64)} chars")
    else:
        print("No charts generated. Check if you have data in the database.")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
