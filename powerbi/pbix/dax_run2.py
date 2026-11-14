"""Run DAX diagnostic query: focus-verified click + clipboard paste + Enter."""
import ctypes
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pbi_win2 import force_focus, window_rect, find_pbi  # noqa

QUERY = 'EVALUATE ROW("revenue", [Total Revenue])'

hwnd, title = find_pbi()
if not hwnd:
    print('NO PBI')
    sys.exit(2)
if not force_focus(hwnd):
    print('FOCUS FAILED')
    sys.exit(3)

user32 = ctypes.windll.user32
l, t_, r, b = window_rect(hwnd)


def click_img(ix, iy):
    user32.SetCursorPos(l + ix, t_ + iy)
    time.sleep(0.2)
    user32.mouse_event(2, 0, 0, 0, 0)
    user32.mouse_event(4, 0, 0, 0, 0)
    time.sleep(0.4)


def key_combo(vk_mod, vk):
    user32.keybd_event(vk_mod, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(vk, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(vk, 0, 2, 0)
    time.sleep(0.05)
    user32.keybd_event(vk_mod, 0, 2, 0)
    time.sleep(0.15)


# 1. focus the editor strip
click_img(600, 360)

# 2. clipboard
subprocess.run(['powershell', '-NoProfile', '-Command',
                f'Set-Clipboard -Value "{QUERY}"'], capture_output=True)
time.sleep(0.5)

# 3. Ctrl+A, Ctrl+V, Enter
key_combo(0x11, 0x41)
key_combo(0x11, 0x56)
time.sleep(0.4)
user32.keybd_event(0x0D, 0, 0, 0)
user32.keybd_event(0x0D, 0, 2, 0)
time.sleep(5)
print('done')
