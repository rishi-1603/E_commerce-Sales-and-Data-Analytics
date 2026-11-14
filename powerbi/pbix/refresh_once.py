"""Invoke the visible banner 'Refresh now' button once, report result."""
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

btns = [c for c in w.descendants()
        if c.element_info.control_type == 'Button'
        and (c.window_text() or '').strip() == 'Refresh now'
        and 340 < c.element_info.rectangle.top < 440]
btns.sort(key=lambda b: b.element_info.rectangle.top)
if not btns:
    print('no banner buttons — banner may be gone already')
    sys.exit(0)
b = btns[0]
print('visible top banner button rect:', b.element_info.rectangle)
b.invoke()
print('Invoke() sent')

time.sleep(5)
# check whether the banner text is still present
try:
    txt = [c for c in w.descendants()
           if c.element_info.control_type == 'Text'
           and 'incomplete or no data' in (c.window_text() or '')]
    print('banner still visible after 5s:', bool(txt))
except Exception as e:
    print('check failed:', e)
