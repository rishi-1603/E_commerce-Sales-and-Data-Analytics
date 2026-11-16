"""Invoke the FIRST 'Refresh now' banner button once, then wait until refresh finishes.

Completion signal: no 'Refresh now' buttons remain in the UIA tree (two
consecutive clean scans). Exit codes: 0 done, 3 timeout, 2 no window.
Uses programmatic invoke() only — never moves the mouse cursor.
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

wins = [(h, t) for h, t in list_windows() if 'ecomanalytics' in t.lower()]
if not wins:
    print('NO PBI WINDOW')
    sys.exit(2)
hwnd = wins[0][0]
u = ctypes.windll.user32
u.ShowWindow(hwnd, 9)
time.sleep(0.5)
u.SetForegroundWindow(hwnd)
time.sleep(1.0)

from pywinauto import Desktop

d = Desktop(backend='uia')
w = d.window(handle=hwnd)


def refresh_buttons():
    return [c for c in w.descendants(control_type='Button')
            if (c.window_text() or '').strip().lower() == 'refresh now']


btns = refresh_buttons()
print('refresh buttons at start:', len(btns))
if not btns:
    print('BANNER ALREADY GONE — model appears loaded')
    sys.exit(0)
try:
    btns[0].invoke()
    print('invoked first Refresh now')
except Exception as e:
    print('invoke failed:', e)
    sys.exit(4)

start = time.time()
clean = 0
while time.time() - start < 225:
    time.sleep(15)
    n = len(refresh_buttons())
    print(f'  t={int(time.time() - start):3d}s  refresh-buttons={n}')
    if n == 0:
        clean += 1
        if clean >= 2:
            print('REFRESH DONE — banner gone')
            sys.exit(0)
    else:
        clean = 0
print('TIMEOUT — banner still present after refresh attempt')
sys.exit(3)
