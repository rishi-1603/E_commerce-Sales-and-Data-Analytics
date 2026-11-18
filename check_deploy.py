import requests
import re

url = 'https://ecom-zeta-one.vercel.app/'
r = requests.get(url, timeout=30)
print(f'Status: {r.status_code}')

idx = r.text.find('function escapeHtml')
if idx >= 0:
    print('escapeHtml found at:', idx)
    snippet = r.text[idx:idx+300]
    print(repr(snippet))
    
    # Check for the buggy pattern
    if "replace(/'/g,'''')" in r.text:
        print('BUGGY pattern found: replace(/'/g,\'\'\')')
    else:
        print('No buggy pattern found')
        
    # Check for the fixed pattern
    if 'replace(/"\'/g,"\'")' in r.text or "replace(/'/g,\"'\")" in r.text:
        print('FIXED pattern found')
    else:
        print('Fixed pattern not clearly found')