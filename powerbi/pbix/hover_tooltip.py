"""Hover over a Data pane field and read the tooltip that appears."""
import ctypes
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from win import list_windows  # noqa
from pbi_win2 import force_focus, window_rect, find_pbi  # noqa

hwnd, title = find_pbi()
if not hwnd:
    print('NO PBI')
    sys.exit(2)

if not force_focus(hwnd):
    print('FOCUS FAILED')
    sys.exit(3)

ix, iy = int(sys.argv[1]), int(sys.argv[2])
l, t_, r, b = window_rect(hwnd)
user32 = ctypes.windll.user32
user32.SetCursorPos(l + ix, t_ + iy)
print('hovering at', l + ix, t_ + iy)
time.sleep(3.0)

# look for tooltip windows
wins = list_windows()
print('--- all visible windows now ---')
for h, t in wins:
    print(h, repr(t[:100]))

# UIA dump of small popups (tooltips)
from pywinauto import Desktop
d = Desktop(backend='uia')
for h, t in wins:
    tl = (t or '').lower()
    if 'tooltip' in tl or ('power bi' in tl and t != title) or t != title:
        try:
            w = d.window(handle=h)
            texts = [c.window_text() for c in w.descendants()
                     if (c.window_text() or '').strip()]
            if texts:
                print('UIA', h, repr(t[:60]), '->', texts[:20])
        except Exception:
            pass
