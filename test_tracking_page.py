import requests
from bs4 import BeautifulSoup

# Test the tracking page
try:
    response = requests.get('http://localhost:8005/track-application')
    print(f"Tracking page status: {response.status_code}")
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check if the tracking form exists
        track_email_input = soup.find('input', {'id': 'trackEmail'})
        track_button = soup.find('button', {'onclick': 'trackApps()'})
        results_div = soup.find('div', {'id': 'trackerResults'})
        
        print(f"Email input found: {track_email_input is not None}")
        print(f"Track button found: {track_button is not None}")
        print(f"Results div found: {results_div is not None}")
        
        # Check if JavaScript is present
        scripts = soup.find_all('script')
        track_function_found = False
        for script in scripts:
            if script.string and 'trackApps' in script.string:
                track_function_found = True
                break
        
        print(f"trackApps function found: {track_function_found}")
        
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")
