import re

html = open("dashboard/dashboard.html", encoding="utf-8").read()
m = re.search(r"const DATA = (\{.*?\});\s*\n\s*const C", html, re.S)
raw = m.group(1)
raw = re.sub(r"([{,]\\s*)([A-Za-z_][A-Za-z0-9_ ]*?)\\s*:", r'\1"\2":', raw)
raw = raw.replace("'", '"')
raw = re.sub(r",\\s*([\\]}])", r"\1", raw)

lines = raw.split("\n")
for i in range(36, 42):
    if i < len(lines):
        print(i + 1, repr(lines[i][:300]))
