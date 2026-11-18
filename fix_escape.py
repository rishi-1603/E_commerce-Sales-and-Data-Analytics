with open('dashboard/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# The correct escapeHtml function - proper JS syntax
# In a single-quoted JS string, to replace single quote with single quote:
# We need: replace(/'/g, "'") 
# But in the HTML file which uses single quotes for JS strings, we need to escape properly
# The JS string is: '...' so inside we use double quotes for the replacement: "'"

correct = """function escapeHtml(text){
  if(!text) return '';
  return String(text).replace(/&/g,'&').replace(/</g,'<').replace(/>/g,'>').replace(/"/g,'"').replace(/'/g,"'");
}"""

import re
content = re.sub(r'function escapeHtml\(text\)\{[^}]+\}', 
                 'function escapeHtml(text){\n  if(!text) return \'\';\n  return String(text).replace(/&/g,\'&\').replace(/</g,\'<\').replace(/>/g,\'>\').replace(/"/g,\'"\').replace(/\'/g,\'"\');\n}',
                 content, flags=re.DOTALL)

with open('dashboard/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed escapeHtml function')