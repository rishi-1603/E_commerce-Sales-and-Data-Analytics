"""Full Save-As-.pbix flow: File > Save as > Recent pbix > dialog: set type .pbix, name, Save."""
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

TEMP = r'C:\Users\user\AppData\Local\Temp\opencode'


def force_focus(hwnd, tries=6):
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


def click_rel(hwnd, ix, iy):
    if not force_focus(hwnd):
        print(f'FOCUS FAILED for {hwnd} - skip click')
        return False
    l, t_, r, b = window_rect(hwnd)
    user32.SetCursorPos(l + ix, t_ + iy)
    time.sleep(0.25)
    user32.mouse_event(2, 0, 0, 0, 0)
    user32.mouse_event(4, 0, 0, 0, 0)
    time.sleep(0.5)
    return True


def grab(hwnd, path):
    from PIL import ImageGrab
    if user32.GetForegroundWindow() != hwnd:
        print('grab: not foreground', path)
        return False
    l, t_, r, b = window_rect(hwnd)
    img = ImageGrab.grab().crop((l, t_, r, b))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return True


def key(vk, du):
    user32.keybd_event(vk, 0, du, 0)
    time.sleep(0.04)


def type_text(s):
    for ch in s:
        vk = user32.VkKeyScanW(ord(ch)) & 0xFF
        if vk == 0xFFFF:
            continue
        key(vk, 0)
        key(vk, 2)
        time.sleep(0.03)


def find_win(substr):
    for h, t in list_windows():
        if substr.lower() in (t or '').lower():
            return h, t
    return None, None


from pywinauto import Desktop
d = Desktop(backend='uia')

# --- 1. main PBI window: File menu ---
hwnd, title = find_win('ecomanalytics')
if not hwnd:
    print('NO PBI WINDOW')
    sys.exit(2)
print('main:', title)
click_rel(hwnd, 60, 75)
time.sleep(2.0)
grab(hwnd, os.path.join(TEMP, 'sa_file.png'))

# --- 2. Save as item ---
click_rel(hwnd, 136, 351)
time.sleep(3.0)

# --- 3. Recent 'pbix' location ---
click_rel(hwnd, 1096, 336)

# --- 4. wait for Save As dialog ---
dlgh = None
for _ in range(20):
    time.sleep(1.0)
    dlgh, dt = find_win('save as')
    if dlgh:
        break
if not dlgh:
    print('NO SAVE AS DIALOG APPEARED')
    sys.exit(3)
print('dialog:', dt)
if not force_focus(dlgh):
    print('DIALOG FOCUS FAILED')
    sys.exit(4)
time.sleep(0.5)

l, t_, r, b = window_rect(dlgh)
print('dialog rect:', l, t_, r, b)

w = d.window(handle=dlgh)

# --- 5. save-as type: select *.pbix item ---
combos = [c for c in w.descendants()
          if c.element_info.control_type == 'ComboBox']
type_combo = None
fn_combo = None
for c in combos:
    nm = (c.element_info.name or '')
    val = (c.window_text() or '')
    if 'save as type' in nm.lower():
        type_combo = c
    if 'file name' in nm.lower():
        fn_combo = c
    print('combo:', repr(nm), '| value:', repr(val[:70]))

if type_combo is None:
    print('NO TYPE COMBO')
    sys.exit(5)

cur = (type_combo.window_text() or '')
print('type current:', cur)
if '.pbix' not in cur.lower():
    type_combo.expand()
    time.sleep(0.8)
    items = [i for i in type_combo.descendants()
             if i.element_info.control_type in ('ListItem', 'ComboBoxItem')]
    names = [i.element_info.name for i in items]
    print('items:', names)
    target = None
    for i in items:
        nm = (i.element_info.name or '').lower()
        if 'pbix' in nm:
            target = i
            break
    if target is None:
        print('NO .pbix ITEM')
        sys.exit(6)
    try:
        target.click_input()
        print('clicked item:', target.element_info.name)
    except Exception as e:
        print('click_input failed:', e, '- trying select()')
        target.select()
    time.sleep(0.6)
    print('type now:', type_combo.window_text())

# --- 6. filename ---
click_abs_x = l + 700
click_abs_y = t_ + 654
user32.SetCursorPos(click_abs_x, click_abs_y)
time.sleep(0.25)
user32.mouse_event(2, 0, 0, 0, 0)
user32.mouse_event(4, 0, 0, 0, 0)
time.sleep(0.4)
key(0x11, 0); key(0x41, 0); key(0x41, 2); key(0x11, 2)
time.sleep(0.2)
type_text('EcomAnalytics')
time.sleep(0.4)

# --- 7. Save ---
user32.SetCursorPos(l + 818, t_ + 771)
time.sleep(0.25)
user32.mouse_event(2, 0, 0, 0, 0)
user32.mouse_event(4, 0, 0, 0, 0)
print('Save clicked')

# --- 8. overwrite confirm + result watch ---
confirmed = False
for attempt in range(10):
    time.sleep(1.5)
    allw = list_windows()
    for h, ttl in allw:
        tl = (ttl or '').lower()
        if 'save as' in tl and h != dlgh:
            try:
                wc = d.window(handle=h)
                yes = [bb for bb in wc.descendants()
                       if bb.element_info.control_type == 'Button'
                       and (bb.element_info.name or '').strip().replace('&', '').lower() == 'yes']
                if yes:
                    r2 = yes[0].element_info.rectangle
                    user32.SetCursorPos((r2.left + r2.right) // 2,
                                        (r2.top + r2.bottom) // 2)
                    time.sleep(0.2)
                    user32.mouse_event(2, 0, 0, 0, 0)
                    user32.mouse_event(4, 0, 0, 0, 0)
                    print('overwrite confirmed')
                    confirmed = True
            except Exception:
                pass
    nh, nt = find_win('ecomanalytics')
    if nt and nt != title:
        print('TITLE CHANGED:', nt)
        break

print('done. overwrite confirmed:', confirmed)
print('final title check...')
time.sleep(2)
_, nt = find_win('ecomanalytics')
print('title:', nt)
