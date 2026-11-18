with open('dashboard/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# The correct escapeHtml function:
# In JavaScript: replace(/'/g, "'") - replaces single quotes with single quotes
# In the HTML file, the JS code is embedded in a single-quoted Python string that generates the HTML
# So we need to properly escape for the Python string that generates JS code

# The correct JS code should be:
# return String(text).replace(/&/g,'&').replace(/</g,'<').replace(/>/g,'>').replace(/"/g,'"').replace(/'/g,"'");

# In the Python string that generates the HTML, we need:
correct_js = r"return String(text).replace(/&/g,'&').replace(/</g,'<').replace(/>/g,'>').replace(/\"/g,'\"').replace(/'/g,\"'\");"

import re
content = re.sub(
    r'function escapeHtml\(text\)\{[^}]+\}',
    'function escapeHtml(text){\n  if(!text) return \'\';\n  ' + correct_js + '\n}',
    content, flags=re.DOTALL
)

with open('dashboard/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed escapeHtml function')