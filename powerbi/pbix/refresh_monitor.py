"""Invoke banner Refresh now, then monitor for progress/error dialogs."""
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
print('candidate banner buttons:', len(btns))
btns.sort(key=lambda b: b.element_info.rectangle.top)
b = btns[0]
print('invoking rect:', b.element_info.rectangle)
b.invoke()
print('invoked. monitoring 90s...')

seen = set()
for i in range(30):
    time.sleep(3)
    cur = set()
    for h, t in list_windows():
        tl = t.lower()
        if any(k in tl for k in ('refresh', 'error', 'issues', 'progress', 'load')):
            cur.add(t)
    new = cur - seen
    if new:
        print(f'[t={i*3}s] NEW WINDOWS:', new)
        seen |= cur
    # also poll banner state via UIA text quickly
    if i in (9, 19, 29):
        try:
            texts = [c.window_text() for c in w.descendants()
                     if c.element_info.control_type == 'Text'
                     and 'incomplete or no data' in (c.window_text() or '')]
            print(f'[t={i*3}s] banner-still-present:', bool(texts))
        except Exception as e:
            print('poll err', e)

print('monitor done')
