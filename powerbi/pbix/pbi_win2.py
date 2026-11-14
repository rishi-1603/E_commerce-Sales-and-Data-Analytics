"""Robust PBI focus + capture + click utilities with foreground VERIFICATION.

Never clicks or sends keys unless the Power BI window is verified foreground.
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
kernel32 = ctypes.windll.kernel32


def find_pbi():
    wins = [(h, t) for h, t in list_windows() if 'ecomanalytics' in t.lower()]
    return wins[0] if wins else (None, None)


def force_focus(hwnd, tries=5):
    """Force-foreground via AttachThreadInput + Alt-key trick; verify."""
    for i in range(tries):
        user32.ShowWindow(hwnd, 9)
        time.sleep(0.4)
        # Alt press/release unlocks SetForegroundWindow for this process
        user32.keybd_event(0x12, 0, 0, 0)
        user32.keybd_event(0x12, 0, 2, 0)
        time.sleep(0.1)
        fg = user32.GetForegroundWindow()
        fg_thread = user32.GetWindowThreadProcessId(fg, None)
        cur_thread = kernel32.GetCurrentThreadId()
        user32.AttachThreadInput(cur_thread, fg_thread, True)
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
        user32.AttachThreadInput(cur_thread, fg_thread, False)
        time.sleep(0.6)
        if user32.GetForegroundWindow() == hwnd:
            return True
    return user32.GetForegroundWindow() == hwnd


def window_rect(hwnd):
    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom


def click_rel(hwnd, ix, iy):
    """Click at window-relative coordinates after verifying focus."""
    if not force_focus(hwnd):
        print('FOCUS FAILED - aborting click')
        return False
    l, t_, r, b = window_rect(hwnd)
    user32.SetCursorPos(l + ix, t_ + iy)
    time.sleep(0.25)
    user32.mouse_event(2, 0, 0, 0, 0)
    user32.mouse_event(4, 0, 0, 0, 0)
    time.sleep(0.5)
    return True


def grab_pbi(hwnd, path):
    """Capture screen and crop to the PBI window (PBI must be foreground)."""
    from PIL import ImageGrab
    if user32.GetForegroundWindow() != hwnd:
        print('NOT FOREGROUND - capture would show wrong window')
        return False
    l, t_, r, b = window_rect(hwnd)
    img = ImageGrab.grab()
    crop = img.crop((l, t_, r, b))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    crop.save(path)
    print('saved', path, crop.size)
    return True


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'focus'
    hwnd, title = find_pbi()
    if not hwnd:
        print('NO PBI WINDOW')
        sys.exit(2)
    if cmd == 'focus':
        ok = force_focus(hwnd)
        print('focus ok:', ok)
    elif cmd == 'click':
        ix, iy = int(sys.argv[2]), int(sys.argv[3])
        ok = click_rel(hwnd, ix, iy)
        print('click ok:', ok)
    elif cmd == 'shot':
        grab_pbi(hwnd, sys.argv[2])
    elif cmd == 'clickshot':
        # click then capture: click <ix> <iy> <path>
        ix, iy = int(sys.argv[2]), int(sys.argv[3])
        ok = click_rel(hwnd, ix, iy)
        if not ok:
            sys.exit(3)
        time.sleep(float(sys.argv[4]) if len(sys.argv) > 4 else 2.0)
        grab_pbi(hwnd, sys.argv[5] if len(sys.argv) > 5 else sys.argv[-1])
