import requests
import re

# Test the live deployment
url = 'https://ecom-zeta-one.vercel.app/'
try:
    r = requests.get(url, timeout=30)
    print(f'{url}: {r.status_code}')
    if 'function nav(' in r.text:
        print('  ✓ nav function present')
    else:
        print('  ✗ nav function NOT FOUND')
    if 'escapeHtml' in r.text:
        print('  ✓ escapeHtml present')
    else:
        print('  ✗ escapeHtml NOT FOUND')
    if 'buildPage' in r.text:
        print('  ✓ buildPage present')
    else:
        print('  ✗ buildPage NOT FOUND')
    nav_calls = len(re.findall(r'nav\(', r.text))
    print(f'nav() calls: {nav_calls}')
    
    # Check for syntax errors in escapeHtml
    if "replace(/'/g,'''')" in r.text:
        print('  ⚠ OLD BUGGY escapeHtml still present')
    elif "replace(/'/g,\"'\")" in r.text or "replace(/'/g,\"'\")" in r.text:
        print('  ✓ FIXED escapeHtml present')
    else:
        print('  ? escapeHtml pattern unclear')
        # Find the escapeHtml function
        idx = r.text.find('function escapeHtml')
        if idx >= 0:
            print('  escapeHtml snippet:', repr(r.text[idx:idx+200]))
except Exception as e:
    print(f'{url}: ERROR - {e}')