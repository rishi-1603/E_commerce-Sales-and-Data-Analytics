"""Capture any window by title substring via UIA (occlusion-safe)."""
import ctypes
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from win import list_windows  # noqa

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

sub = sys.argv[1].lower()
path = sys.argv[2]
wins = [(h, t) for h, t in list_windows() if sub in (t or '').lower()]
if not wins:
    print('NO WINDOW matching', sub)
    sys.exit(2)
hwnd, title = wins[0]

from pywinauto import Desktop
d = Desktop(backend='uia')
w = d.window(handle=hwnd)
img = w.capture_as_image()
os.makedirs(os.path.dirname(path), exist_ok=True)
img.save(path)
print('saved', path, img.size, '| title:', title)
