"""Restore the 'Issues were found' dialog and dump its text via UIA."""
import ctypes, time
import sys
sys.path.insert(0, r'C:\Users\user\portfolio-roadmaps\repos\ecom\powerbi\pbix')
from win import list_windows  # noqa

user32 = ctypes.windll.user32

wins = list_windows()
dlg = [(h, t) for h, t in wins if 'issues were found' in t.lower()]
print('dialogs found:', dlg)
if not dlg:
    sys.exit(2)

hwnd = dlg[0][0]
user32.ShowWindow(hwnd, 9)  # SW_RESTORE
time.sleep(1.0)

from pywinauto import Desktop
d = Desktop(backend='uia')
window = d.window(handle=hwnd)
for c in window.descendants():
    t = (c.window_text() or '').strip()
    if t and len(t) > 3:
        print(c.element_info.control_type, '|', t[:300])
