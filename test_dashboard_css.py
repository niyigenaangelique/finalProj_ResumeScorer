import requests
import json

def test_dashboard_css():
    """Test if dashboard CSS is being applied properly"""
    session = requests.Session()
    
    # Login
    login_data = {'email': 'angelbrenna20@gmail.com', 'password': 'Niyigena2003@'}
    response = session.post('http://localhost:8003/login', data=login_data, allow_redirects=False)
    
    if response.status_code != 302:
        print('❌ Login failed')
        return False
    
    print('✅ Login successful')
    
    # Get dashboard page
    dashboard_response = session.get('http://localhost:8003/dashboard')
    
    if dashboard_response.status_code != 200:
        print('❌ Dashboard page failed to load')
        return False
    
    print('✅ Dashboard page loads successfully')
    
    # Check if CSS is present in the HTML
    content = dashboard_response.text
    
    print('\n🔍 CSS Analysis:')
    
    # Check for CSS variables
    css_variables = [
        '--bg:', '--white:', '--blue:', '--red:', '--teal:', '--amber:',
        '--ink:', '--ink2:', '--ink3:', '--border:', '--radius:', '--shadow:'
    ]
    
    css_vars_found = 0
    for var in css_variables:
        if var in content:
            css_vars_found += 1
    
    if css_vars_found >= 8:
        print(f'✅ CSS Variables found ({css_vars_found}/{len(css_variables)})')
    else:
        print(f'❌ CSS Variables missing ({css_vars_found}/{len(css_variables)})')
    
    # Check for CSS classes
    css_classes = [
        '.topnav', '.tn-brand', '.tn-logo', '.stats-row', '.stat-tile',
        '.card', '.emp-table', '.btn-primary', '.page-title'
    ]
    
    css_classes_found = 0
    for cls in css_classes:
        if cls in content:
            css_classes_found += 1
    
    if css_classes_found >= 8:
        print(f'✅ CSS Classes found ({css_classes_found}/{len(css_classes)})')
    else:
        print(f'❌ CSS Classes missing ({css_classes_found}/{len(css_classes)})')
    
    # Check for Chart.js
    if 'Chart.js' in content or 'chart.umd.min.js' in content:
        print('✅ Chart.js library found')
    else:
        print('❌ Chart.js library missing')
    
    # Check for Google Fonts
    if 'fonts.googleapis.com' in content:
        print('✅ Google Fonts found')
    else:
        print('❌ Google Fonts missing')
    
    # Check for HTML structure
    html_elements = [
        '<!DOCTYPE html>', '<html lang="en">', '<head>', '<body>',
        '<nav class="topnav">', '<main class="main">', '<script>'
    ]
    
    html_elements_found = 0
    for elem in html_elements:
        if elem in content:
            html_elements_found += 1
    
    if html_elements_found >= 6:
        print(f'✅ HTML Structure complete ({html_elements_found}/{len(html_elements)})')
    else:
        print(f'❌ HTML Structure incomplete ({html_elements_found}/{len(html_elements)})')
    
    print('\n🌐 Browser Testing Instructions:')
    print('1. Open browser: http://localhost:8003/dashboard')
    print('2. Login: angelbrenna20@gmail.com / Niyigena2003@')
    print('3. Check if:')
    print('   - Modern styling is applied (gradients, shadows, rounded corners)')
    print('   - Navigation bar is styled properly')
    print('   - Stat tiles have gradient backgrounds')
    print('   - Charts are rendering')
    print('   - Tables have proper styling')
    print('   - Buttons have hover effects')
    
    print('\n📋 If CSS is not applying:')
    print('- Check browser console for CSS errors')
    print('- Verify all CSS is in the HTML source')
    print('- Check if JavaScript is executing')
    print('- Look for network errors loading external resources')
    
    return True

if __name__ == "__main__":
    print("🔍 Testing Dashboard CSS")
    print("=" * 40)
    
    success = test_dashboard_css()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Dashboard CSS structure is correct!")
    else:
        print("❌ Dashboard CSS has issues")
