import requests

# Test the dashboard deployment directly
url = 'https://dashboard-psi-smoky-24.vercel.app/'
r = requests.get(url, timeout=30)
print(f'Dashboard deployment: {r.status_code}')

# Check escapeHtml
if "replace(/'/g,'''')" in r.text:
    print('  ⚠ OLD BUGGY escapeHtml present in dashboard deployment')
elif "replace(/'/g,\"'\")" in r.text:
    print('  ✓ FIXED escapeHtml present in dashboard deployment')
else:
    print('  ? escapeHtml pattern unclear')
    idx = r.text.find('function escapeHtml')
    if idx >= 0:
        print('  escapeHtml snippet:', repr(r.text[idx:idx+200]))