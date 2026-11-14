"""Click 'Refresh now' banner button(s) in Power BI Desktop via UIA invoke."""
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
        and (c.window_text() or '').strip() == 'Refresh now']
print('refresh buttons found:', len(btns))
for b in btns:
    try:
        b.invoke()
        print('invoked:', b.element_info.name)
        time.sleep(1.0)
    except Exception as e:
        print('invoke failed:', e)
