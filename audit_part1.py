"""Ecom Project Comprehensive Audit - Part 1: Repository Investigation"""
import os, json

repos = r'C:\Users\user\portfolio-roadmaps\repos\ecom'

print("=" * 60)
print("PART 1: REPOSITORY INVESTIGATION")
print("=" * 60)

# Root directory
print("\nRoot directory contents:")
for item in sorted(os.listdir(repos)):
    if not item.startswith('.'):
        print(f"  {item}")

# Key directories
print("\nKey directories:")
key_dirs = ['powerbi', 'python', 'data', 'sql', 'tests', 'dashboard']
for d in key_dirs:
    dp = os.path.join(repos, d)
    if os.path.isdir(dp):
        items = os.listdir(dp)
        print(f"  {d}/: {len(items)} items")
        # Show first 3
        for item in items[:3]:
            print(f"    - {item}")
        if len(items) > 3:
            print(f"    ... and {len(items)-3} more")

# Power BI specific
print("\nPower BI directory:")
pw = os.path.join(repos, 'powerbi')
if os.path.isdir(pw):
    for item in sorted(os.listdir(pw)):
        print(f"  {item}")

# SQL
print("\nSQL directory:")
sql = os.path.join(repos, 'sql')
if os.path.isdir(sql):
    for item in sorted(os.listdir(sql)):
        print(f"  {item}")

# Data
print("\nData directory:")
dat = os.path.join(repos, 'data')
if os.path.isdir(dat):
    for item in sorted(os.listdir(dat)):
        print(f"  {item}")

# Tests
print("\nTests directory:")
tes = os.path.join(repos, 'tests')
if os.path.isdir(tes):
    for item in sorted(os.listdir(tes)):
        print(f"  {item}")

# Check the .pbix file
print("\nPBIX file info:")
pbix = os.path.join(repos, 'powerbi', 'pbix', 'EcomAnalytics.pbix')
if os.path.exists(pbix):
    size = os.path.getsize(pbix)
    print(f"  EcomAnalytics.pbix: {size:,} bytes")

# Check ZIP
print("\nZIP file info:")
zip_path = r'C:\Users\user\Desktop\EcomProject_2026-11-14.zip'
if os.path.exists(zip_path):
    import zipfile
    z = zipfile.ZipFile(zip_path)
    print(f"  ZIP: {os.path.getsize(zip_path):,} bytes, {len(z.namelist())} entries")
    # Check for pbix in zip
    for n in z.namelist():
        if 'EcomAnalytics' in n:
            print(f"    Found in ZIP: {n}")

PYEOF