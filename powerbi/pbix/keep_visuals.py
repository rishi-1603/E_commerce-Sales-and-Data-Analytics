"""Keep only the named visuals on a page (the rest are moved to a scratch folder).

Usage: python keep_visuals.py "Executive Overview" KPI_1 KPI_2 ...
"""
import json
import os
import shutil
import sys

DEF = r"C:\Users\user\portfolio-roadmaps\repos\ecom\powerbi\pbix\EcomAnalytics.Report\definition"
STASH = r"C:\Users\user\AppData\Local\Temp\opencode\stash_visuals"

page_name = sys.argv[1]
keep = set(sys.argv[2:])

pages_root = os.path.join(DEF, "pages")
target = None
for name in os.listdir(pages_root):
    pj = os.path.join(pages_root, name, "page.json")
    if os.path.isfile(pj):
        with open(pj, encoding="utf-8") as f:
            if json.load(f).get("displayName") == page_name:
                target = os.path.join(pages_root, name)
                break
if target is None:
    print("page not found:", page_name)
    sys.exit(2)

vis_root = os.path.join(target, "visuals")
os.makedirs(STASH, exist_ok=True)
kept, moved = [], []
for v in sorted(os.listdir(vis_root)):
    vj = os.path.join(vis_root, v, "visual.json")
    with open(vj, encoding="utf-8") as f:
        nm = json.load(f)["name"]
    if any(k in nm for k in keep):
        kept.append(nm)
    else:
        shutil.move(os.path.join(vis_root, v), os.path.join(STASH, v))
        moved.append(nm)

print(f"{page_name}: kept {len(kept)} -> {kept}")
print(f"moved out {len(moved)} -> {moved}")
