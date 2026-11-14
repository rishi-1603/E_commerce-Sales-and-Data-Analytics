"""Drag the DAX editor/results split divider to grow the editor pane."""
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

# divider: thin strip between Run button row and Results header
start_y = t_ + int(sys.argv[1]) if len(sys.argv) > 1 else t_ + 352
end_y = t_ + int(sys.argv[2]) if len(sys.argv) > 2 else t_ + 150
x = l + 700

user32.SetCursorPos(x, start_y)
time.sleep(0.3)
user32.mouse_event(2, 0, 0, 0, 0)  # down
time.sleep(0.2)
steps = 12
for i in range(1, steps + 1):
    y = start_y + (end_y - start_y) * i // steps
    user32.SetCursorPos(x, y)
    time.sleep(0.03)
user32.mouse_event(4, 0, 0, 0, 0)  # up
time.sleep(1.0)
print('dragged', start_y, '->', end_y)
