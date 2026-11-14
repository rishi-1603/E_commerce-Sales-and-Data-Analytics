"""Click the VISIBLE 'Refresh now' button via its UIA screen rect."""
import ctypes
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from win import list_windows  # noqa

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

user32 = ctypes.windll.user32

wins = [(h, t) for h, t in list_windows() if 'ecomanalytics' in t.lower()]
if not wins:
    print('NO PBI WINDOW')
    sys.exit(2)
hwnd = wins[0][0]

from pywinauto import Desktop
d = Desktop(backend='uia')
w = d.window(handle=hwnd)

# bring window forward first
user32.ShowWindow(hwnd, 9)
time.sleep(0.5)
user32.SetForegroundWindow(hwnd)
time.sleep(1.0)

btns = [c for c in w.descendants()
        if c.element_info.control_type == 'Button'
        and (c.window_text() or '').strip() == 'Refresh now']

clicked = 0
for b in btns:
    try:
        r = b.element_info.rectangle
        # only click buttons in the banner area (top of window, y < 350)
        if r.top < 350 and r.bottom > r.top and r.right > r.left:
            cx = (r.left + r.right) // 2
            cy = (r.top + r.bottom) // 2
            user32.SetCursorPos(cx, cy)
            time.sleep(0.2)
            user32.mouse_event(2, 0, 0, 0, 0)
            user32.mouse_event(4, 0, 0, 0, 0)
            time.sleep(2.0)
            clicked += 1
            print(f'clicked Refresh now at ({cx},{cy}) rect=({r.left},{r.top},{r.right},{r.bottom})')
            break  # one click should trigger the full refresh
    except Exception as e:
        print('skip:', e)

print('clicked count:', clicked)
