"""Run a DAX query in Power BI's DAX query view via clipboard paste + Enter."""
import ctypes
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from win import list_windows  # noqa

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

user32 = ctypes.windll.user32

QUERY = 'EVALUATE ROW("revenue", [Total Revenue])'

wins = [(h, t) for h, t in list_windows() if 'ecomanalytics' in t.lower()]
if not wins:
    print('NO PBI WINDOW')
    sys.exit(2)
hwnd = wins[0][0]

# minimize others so SetForegroundWindow works
for h, t in list_windows():
    tl = t.lower()
    if any(k in tl for k in ('power bi', 'ecomanalytics', 'program manager')):
        continue
    user32.ShowWindow(h, 6)
time.sleep(0.8)
user32.ShowWindow(hwnd, 9)
time.sleep(0.5)
user32.SetForegroundWindow(hwnd)
time.sleep(1.2)


def key(vk, down_up=None):
    user32.keybd_event(vk, 0, 0, 0)
    user32.keybd_event(vk, 0, 2, 0)


def click_img(ix, iy):
    l, t_, r, b = 100, 100, 1820, 920
    user32.SetCursorPos(l + ix, t_ + iy)
    time.sleep(0.2)
    user32.mouse_event(2, 0, 0, 0, 0)
    user32.mouse_event(4, 0, 0, 0, 0)


# 1. set clipboard
r = subprocess.run(['powershell', '-NoProfile', '-Command',
                    f'Set-Clipboard -Value "{QUERY}"'], capture_output=True)
time.sleep(0.5)

# 2. click into the editor
click_img(600, 390)
time.sleep(0.8)

# 3. select all + paste
key(0x11)  # ctrl handled inside key(): need down/up separately — use simple pairs
# proper: ctrl down, A down/up, ctrl up
user32.keybd_event(0x11, 0, 0, 0)
key(0x41)
user32.keybd_event(0x11, 0, 2, 0)
time.sleep(0.3)
user32.keybd_event(0x11, 0, 0, 0)
key(0x56)  # V
user32.keybd_event(0x11, 0, 2, 0)
time.sleep(0.5)

# 4. run query with Enter
key(0x0D)
time.sleep(4)
print('query pasted & run')
