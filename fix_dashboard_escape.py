with open('dashboard/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# The issue: replace(/'/g,'''') - three single quotes is invalid JS
# Fix: replace(/'/g,"'") - replace single quote with single quote (properly escaped in double-quoted string)
old = "replace(/'/g,'''')"
new = 'replace(/"\'/g,"\\\'")'

if old in content:
    content = content.replace(old, new)
    print("Fixed escapeHtml in dashboard/dashboard.html")
else:
    print("Pattern not found")
    idx = content.find('function escapeHtml')
    if idx >= 0:
        print(content[idx:idx+200])

with open('dashboard/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")