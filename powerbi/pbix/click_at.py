"""Click image-relative coordinates inside the Power BI window (handles DPI)."""
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


def window_rect(hwnd):
    r = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom


def click_abs(x, y):
    user32.SetCursorPos(x, y)
    time.sleep(0.15)
    user32.mouse_event(2, 0, 0, 0, 0)
    user32.mouse_event(4, 0, 0, 0, 0)


if __name__ == '__main__':
    title_sub = sys.argv[1].lower()
    ix, iy = int(sys.argv[2]), int(sys.argv[3])  # coords inside window image
    wins = [(h, t) for h, t in list_windows() if title_sub in t.lower()]
    if not wins:
        print('NO WINDOW')
        sys.exit(2)
    hwnd = wins[0][0]
    user32.ShowWindow(hwnd, 9)
    time.sleep(0.5)
    user32.SetForegroundWindow(hwnd)
    time.sleep(1.0)
    l, t_, r, b = window_rect(hwnd)
    print('window rect:', l, t_, r, b, 'size:', r - l, b - t_)
    # image coords are relative to window client area; approximate with window origin
    sx, sy = l + ix, t_ + iy
    print('clicking screen', sx, sy)
    click_abs(sx, sy)
    print('done')
