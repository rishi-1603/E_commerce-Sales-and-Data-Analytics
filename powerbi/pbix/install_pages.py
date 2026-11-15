"""Install a subset of the generated PBIR pages into the live report definition.

Usage: python install_pages.py "Executive Overview" ["Sales Performance" ...]
"""
import json
import os
import shutil
import sys

DEF = r"C:\Users\user\portfolio-roadmaps\repos\ecom\powerbi\pbix\EcomAnalytics.Report\definition"
BAK = r"C:\Users\user\AppData\Local\Temp\opencode\pbir_gen"
PAGES_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json"

want = sys.argv[1:]
if not want:
    print("usage: install_pages.py <page display name> [...]")
    sys.exit(1)

# map display name -> folder in the backup
by_name = {}
for name in os.listdir(os.path.join(BAK, "pages")):
    pj = os.path.join(BAK, "pages", name, "page.json")
    if os.path.isfile(pj):
        with open(pj, encoding="utf-8") as f:
            by_name[json.load(f)["displayName"]] = name

missing = [w for w in want if w not in by_name]
if missing:
    print("unknown pages:", missing, "| available:", list(by_name))
    sys.exit(2)

live = os.path.join(DEF, "pages")
if os.path.isdir(live):
    shutil.rmtree(live)
os.makedirs(live)

order = []
for w in want:
    folder = by_name[w]
    shutil.copytree(os.path.join(BAK, "pages", folder), os.path.join(live, folder))
    order.append(folder)

with open(os.path.join(live, "pages.json"), "w", encoding="utf-8") as f:
    json.dump({"$schema": PAGES_SCHEMA, "pageOrder": order, "activePageName": order[0]},
              f, indent=2)

print(f"installed {len(order)} page(s):", ", ".join(want))
print("visuals:", sum(len(os.listdir(os.path.join(live, p, "visuals"))) for p in order))
