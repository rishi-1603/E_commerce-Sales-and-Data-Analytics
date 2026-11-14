"""List all top-level windows; focus the Power BI window; optionally click coords."""
import sys, time, ctypes
from ctypes import wintypes

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

user32 = ctypes.windll.user32
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)


def list_windows():
    out = []
    @EnumWindowsProc
    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            if n:
                buf = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(hwnd, buf, n + 1)
                out.append((hwnd, buf.value))
        return True
    user32.EnumWindows(cb, 0)
    return out


def focus_pbi():
    wins = list_windows()
    pbi = [(h, t) for h, t in wins if 'power bi desktop' in t.lower() or 'ecomanalytics' in t.lower()]
    if not pbi:
        print('NO PBI WINDOW; visible windows:')
        for h, t in wins:
            print('   ', h, repr(t[:80]))
        sys.exit(2)
    hwnd, title = pbi[0]
    SW_RESTORE = 9
    user32.ShowWindow(hwnd, SW_RESTORE)
    time.sleep(0.5)
    user32.SetForegroundWindow(hwnd)
    time.sleep(1.0)
    print('focused:', hwnd, repr(title))


def minimize_others():
    """Minimize every visible top-level window that is not ours."""
    keep = ('power bi', 'ecomanalytics', 'program manager', 'windows shell', 'greeting')
    for h, t in list_windows():
        tl = t.lower()
        if any(k in tl for k in keep):
            continue
        user32.ShowWindow(h, 6)  # SW_MINIMIZE
    time.sleep(0.5)
    print('minimized others')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'focus'
    if cmd == 'list':
        for h, t in list_windows():
            print(h, repr(t[:90]))
    elif cmd == 'focus':
        focus_pbi()
    elif cmd == 'solo':
        minimize_others()
        focus_pbi()
    elif cmd == 'click':
        # click <title-substr> <x> <y>
        tl_target = sys.argv[2].lower()
        wins = list_windows()
        target = [(h, t) for h, t in wins if tl_target in t.lower()]
        if not target:
            print('NO WINDOW matching', tl_target)
            sys.exit(2)
        h, t = target[0]
        user32.ShowWindow(h, 9)
        time.sleep(0.4)
        user32.SetForegroundWindow(h)
        time.sleep(0.8)
        x, y = int(sys.argv[3]), int(sys.argv[4])
        user32.SetCursorPos(x, y)
        time.sleep(0.2)
        user32.mouse_event(2, 0, 0, 0, 0)
        user32.mouse_event(4, 0, 0, 0, 0)
        print('clicked', x, y, 'on', repr(t))
