"""Strip UTF-8 BOMs from every TMDL / PBIR / PBISM file in the Power BI project.

Power BI refuses to read project files that start with a BOM
("Only text with UTF8 encoding without BOM is supported").
"""
import os

ROOT = r"C:\Users\user\portfolio-roadmaps\repos\ecom\powerbi\pbix"
EXTS = {".tmdl", ".json", ".pbir", ".pbism"}

fixed = []
for base, _, files in os.walk(ROOT):
    if ".git" in base:
        continue
    for name in files:
        if os.path.splitext(name)[1].lower() not in EXTS:
            continue
        path = os.path.join(base, name)
        with open(path, "rb") as f:
            raw = f.read()
        if raw.startswith(b"\xef\xbb\xbf"):
            with open(path, "wb") as f:
                f.write(raw[3:])
            fixed.append(os.path.relpath(path, ROOT))

print(f"stripped BOM from {len(fixed)} file(s)")
for p in fixed:
    print("  -", p)
