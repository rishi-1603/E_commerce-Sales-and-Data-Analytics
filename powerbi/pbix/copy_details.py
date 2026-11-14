"""Click 'Copy details to clipboard' on the Issues dialog, then print clipboard text."""
import ctypes, time, sys
sys.path.insert(0, r'C:\Users\user\portfolio-roadmaps\repos\ecom\powerbi\pbix')
from win import list_windows  # noqa

user32 = ctypes.windll.user32

wins = list_windows()
dlg = [(h, t) for h, t in wins if 'issues were found' in t.lower()]
if not dlg:
    print('no dialog')
    sys.exit(2)
hwnd = dlg[0][0]
user32.ShowWindow(hwnd, 9)
time.sleep(0.8)

from pywinauto import Desktop
d = Desktop(backend='uia')
window = d.window(handle=hwnd)
btn = window.child_window(title='Copy details to clipboard', control_type='Button')
btn.invoke()
time.sleep(1.5)

r = __import__('subprocess').run(['powershell', '-NoProfile', '-Command', 'Get-Clipboard'],
                                 capture_output=True, text=True)
print(r.stdout)
