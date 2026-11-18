import requests

url = 'https://ecom-zeta-one.vercel.app/'
r = requests.get(url, timeout=30)
print('Status:', r.status_code)

# Check for the fixed pattern
if "replace(/'/g,'\"')" in r.text:
    print('FIXED pattern found')
elif "replace(/'/g,'''')" in r.text:
    print('BUGGY pattern found')
else:
    print('Pattern unclear')
    idx = r.text.find("replace(/'/g")
    if idx >= 0:
        print('Found at idx:', idx)
        print(repr(r.text[idx:idx+50]))