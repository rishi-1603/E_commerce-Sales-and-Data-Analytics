"""Click 'Refresh now' via pywinauto click_input (handles UWP + DPI)."""
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

# minimize others so focus switching works
for h, t in list_windows():
    tl = t.lower()
    if any(k in tl for k in ('power bi', 'ecomanalytics', 'program manager', 'greeting')):
        continue
    user32.ShowWindow(h, 6)
time.sleep(0.5)

from pywinauto import Desktop
d = Desktop(backend='uia')
w = d.window(handle=hwnd)

btns = [c for c in w.descendants()
        if c.element_info.control_type == 'Button'
        and (c.window_text() or '').strip() == 'Refresh now'
        and c.element_info.rectangle.top > 0]
print('visible buttons:', len(btns))
for b in btns:
    r = b.element_info.rectangle
    print('rect:', r.left, r.top, r.right, r.bottom)

# click the topmost banner button
if btns:
    btns.sort(key=lambda b: b.element_info.rectangle.top)
    target = btns[0]
    try:
        target.click_input()
        print('click_input OK on', target.element_info.rectangle)
    except Exception as e:
        print('click_input failed:', e)
        # fallback: set focus then invoke
        try:
            w.set_focus()
            target.invoke()
            print('fallback invoke OK')
        except Exception as e2:
            print('fallback invoke failed:', e2)
