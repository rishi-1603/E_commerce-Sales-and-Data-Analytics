"""Hover at window-relative coords, wait for tooltip, capture window."""
import ctypes
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pbi_win2 import find_pbi, force_focus, window_rect  # noqa

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

hwnd, _ = find_pbi()
if not hwnd:
    print('NO PBI WINDOW')
    sys.exit(2)
if not force_focus(hwnd):
    print('FOCUS FAILED')
    sys.exit(3)

ix, iy = int(sys.argv[1]), int(sys.argv[2])
path = sys.argv[3]
l, t, r, b = window_rect(hwnd)
ctypes.windll.user32.SetCursorPos(l + ix, t + iy)
time.sleep(1.6)

from PIL import ImageGrab
img = ImageGrab.grab().crop((l, t, r, b))
# crop to a tooltip-friendly region around the cursor
cx = min(max(ix - 260, 0), (r - l) - 520)
cy = min(max(iy - 40, 0), (b - t) - 90)
img.crop((cx, cy, cx + 520, cy + 90)).save(path)
print('saved', path)
