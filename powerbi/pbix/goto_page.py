"""Switch the Power BI report to a page by invoking its page-tab button.

Usage: goto_page.py <page display name>  (e.g. 'Sales Performance')
Then capture with shot_pbi.py. Invoke() only — no cursor movement.
"""
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

u = ctypes.windll.user32
page = sys.argv[1] if len(sys.argv) > 1 else 'Executive Overview'

wins = [(h, t) for h, t in list_windows() if 'ecomanalytics' in t.lower()]
if not wins:
    print('NO PBI WINDOW')
    sys.exit(2)
hwnd = wins[0][0]
u.ShowWindow(hwnd, 9)
time.sleep(0.5)
u.SetForegroundWindow(hwnd)
time.sleep(1.0)

from pywinauto import Desktop

d = Desktop(backend='uia')
w = d.window(handle=hwnd)
btns = [c for c in w.descendants()
        if c.element_info.control_type in ('Button', 'TabItem')
        and (c.window_text() or '').strip() == page]
print('page buttons matching:', len(btns))
if not btns:
    names = sorted({(c.window_text() or '').strip() for c in w.descendants(control_type='Button')})
    print([n for n in names if n][:40])
    sys.exit(4)
try:
    btns[0].invoke()
    print('invoked page tab:', page)
except Exception:
    try:
        btns[0].select()
        print('selected page tab:', page)
    except Exception as e:
        print('invoke and select failed:', e)
        sys.exit(4)
time.sleep(8)
print('page switched')
