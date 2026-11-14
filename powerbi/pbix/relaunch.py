"""Close Power BI Desktop cleanly, then relaunch with the fixed .pbip."""
import subprocess, time, sys

# kill existing Power BI Desktop
r = subprocess.run(['taskkill', '/F', '/IM', 'pbidesktop.exe'], capture_output=True, text=True)
print('kill:', r.returncode, r.stdout.strip(), r.stderr.strip())
time.sleep(5)

# relaunch
subprocess.Popen(['cmd', '/c', 'start', '', r'C:\Users\user\portfolio-roadmaps\repos\ecom\powerbi\pbix\EcomAnalytics.pbip'], shell=False)
print('relaunched')
