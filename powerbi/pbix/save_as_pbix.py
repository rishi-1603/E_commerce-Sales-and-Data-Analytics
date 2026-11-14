"""Save the open Power BI project as a .pbix file via UI automation.

Flow:
  1. Find the Power BI Desktop window
  2. Bring it forward (minimize others first — SetForegroundWindow is blocked
     for background processes otherwise)
  3. Press F12 (Save As shortcut in Power BI Desktop)
  4. Drive the Save As dialog: filename, type=.pbix, save, confirm overwrite
"""
import ctypes
import ctypes.wintypes as wintypes
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
OUT_PATH = r"C:\Users\user\portfolio-roadmaps\repos\ecom\powerbi\pbix\EcomAnalytics.pbix"
OUT_DIR = os.path.dirname(OUT_PATH)
OUT_NAME = os.path.basename(OUT_PATH)


def find_pbi():
    for h, t in list_windows():
        if 'power bi desktop' in t.lower():
            return h, t
    return None, None


def focus(hwnd):
    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    time.sleep(0.6)
    user32.SetForegroundWindow(hwnd)
    time.sleep(1.2)


def key(vk, extra=0):
    user32.keybd_event(vk, 0, extra | 0, 0)
    user32.keybd_event(vk, 0, extra | 2, 0)  # key up


def type_text(s):
    import win32clipboard  # may not exist; fall back to SendInput-less approach
    raise SystemExit
