"""Drive Save As dialog with keyboard input: click name field, type, Save, Yes."""
import ctypes
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from win import list_windows  # noqa
from pbi_win2 import window_rect  # noqa

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


def force_focus(hwnd, tries=5):
    for _ in range(tries):
        user32.ShowWindow(hwnd, 9)
        time.sleep(0.3)
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
        time.sleep(0.5)
        if user32.GetForegroundWindow() == hwnd:
            return True
    return user32.GetForegroundWindow() == hwnd


def click_abs(x, y):
    user32.SetCursorPos(x, y)
    time.sleep(0.2)
    user32.mouse_event(2, 0, 0, 0, 0)
    user32.mouse_event(4, 0, 0, 0, 0)
    time.sleep(0.4)


def key(vk, du):
    user32.keybd_event(vk, 0, du, 0)
    time.sleep(0.04)


def type_text(s):
    vkmap = {}
    for ch in 'abcdefghijklmnopqrstuvwxyz0123456789':
        vkmap[ch] = user32.VkKeyScanW(ord(ch)) & 0xFF
    for ch in s:
        vk = vkmap.get(ch.lower())
        if vk is None:
            continue
        key(vk, 0)
        key(vk, 2)
        time.sleep(0.03)


wins = [(h, t) for h, t in list_windows() if t.strip().lower() == 'save as']
if not wins:
    print('NO SAVE AS DIALOG')
    sys.exit(2)
hwnd = wins[0][0]
if not force_focus(hwnd):
    print('FOCUS FAILED')
    sys.exit(3)

l, t_, r, b = window_rect(hwnd)
print('dialog rect:', l, t_, r, b)

# click into the filename field (center of File name combo)
click_abs(l + 700, t_ + 654)
# select all, type filename
key(0x11, 0); key(0x41, 0); key(0x41, 2); key(0x11, 2)
time.sleep(0.2)
type_text('EcomAnalytics')
time.sleep(0.4)
print('filename typed')

# click Save (center of Save button)
click_abs(l + 818, t_ + 771)
print('Save clicked; scanning for overwrite popup...')

# scan for overwrite confirmation
confirmed = False
from pywinauto import Desktop
d = Desktop(backend='uia')
for attempt in range(8):
    time.sleep(1.5)
    allw = list_windows()
    for h, ttl in allw:
        tl = (ttl or '').lower()
        if 'save as' in tl or 'confirm' in tl:
            try:
                wc = d.window(handle=h)
                yes = [bb for bb in wc.descendants()
                       if bb.element_info.control_type == 'Button'
                       and (bb.element_info.name or '').strip().replace('&', '').lower() == 'yes']
                if yes:
                    print('found Yes button in', ttl)
                    r2 = yes[0].element_info.rectangle
                    click_abs((r2.left + r2.right) // 2, (r2.top + r2.bottom) // 2)
                    print('overwrite confirmed')
                    confirmed = True
                    break
            except Exception as e:
                print('scan err:', e)
    if confirmed:
        break

print('done. confirmed:', confirmed)
