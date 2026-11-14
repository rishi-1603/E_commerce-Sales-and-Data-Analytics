"""Hover over a canvas point without clicking, then capture the window."""
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
wait = float(sys.argv[3]) if len(sys.argv) > 3 else 3.5
path = sys.argv[4] if len(sys.argv) > 4 else os.path.join(
    os.environ['TEMP'], 'opencode', 'pbi_hover.png')

user32.SetCursorPos(l + ix, t_ + iy)
time.sleep(0.3)
# tiny jiggle to trigger tooltip tracking
user32.SetCursorPos(l + ix + 2, t_ + iy)
user32.SetCursorPos(l + ix, t_ + iy)
time.sleep(wait)
grab_pbi(hwnd, path)
