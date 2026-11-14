"""Drag a field from the Data pane onto the report canvas (focus-verified)."""
import ctypes
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pbi_win2 import force_focus, window_rect, find_pbi  # noqa

hwnd, title = find_pbi()
if not hwnd:
    print('NO PBI')
    sys.exit(2)
if not force_focus(hwnd):
    print('FOCUS FAILED')
    sys.exit(3)

user32 = ctypes.windll.user32
l, t_, r, b = window_rect(hwnd)

sx, sy = int(sys.argv[1]), int(sys.argv[2])   # source (image coords)
dx, dy = int(sys.argv[3]), int(sys.argv[4])   # dest (image coords)

p1 = (l + sx, t_ + sy)
p2 = (l + dx, t_ + dy)

user32.SetCursorPos(*p1)
time.sleep(0.4)
user32.mouse_event(2, 0, 0, 0, 0)  # down
time.sleep(0.3)
steps = 18
for i in range(1, steps + 1):
    x = p1[0] + (p2[0] - p1[0]) * i // steps
    y = p1[1] + (p2[1] - p1[1]) * i // steps
    user32.SetCursorPos(x, y)
    time.sleep(0.04)
time.sleep(0.4)
user32.mouse_event(4, 0, 0, 0, 0)  # up
time.sleep(3.0)
print('dragged', p1, '->', p2)
