"""Scroll the Data pane with the mouse wheel (focus-verified)."""
import ctypes
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pbi_win2 import force_focus, window_rect, find_pbi, grab_pbi  # noqa

hwnd, title = find_pbi()
if not hwnd:
    print('NO PBI')
    sys.exit(2)
if not force_focus(hwnd):
    print('FOCUS FAILED')
    sys.exit(3)

user32 = ctypes.windll.user32
l, t_, r, b = window_rect(hwnd)
ix, iy = int(sys.argv[1]), int(sys.argv[2])
notches = int(sys.argv[3])  # negative = scroll down
path = sys.argv[4] if len(sys.argv) > 4 else None

user32.SetCursorPos(l + ix, t_ + iy)
time.sleep(0.4)
for _ in range(abs(notches)):
    user32.mouse_event(0x0800, 0, 0, notches * 120 // abs(notches), 0)
    time.sleep(0.25)
time.sleep(1.0)
print('scrolled', notches, 'notches')
if path:
    grab_pbi(hwnd, path)
