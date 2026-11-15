import ctypes, os, sys, time
sys.path.insert(0, r"C:\Users\user\portfolio-roadmaps\repos\ecom\powerbi\pbix")
from win import list_windows
from pbi_win2 import window_rect
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
def force_focus(hwnd):
    for _ in range(8):
        user32.ShowWindow(hwnd, 9); time.sleep(0.3)
        fg = user32.GetForegroundWindow()
        ft = user32.GetWindowThreadProcessId(fg, None)
        ct = kernel32.GetCurrentThreadId()
        user32.AttachThreadInput(ct, ft, True)
        user32.BringWindowToTop(hwnd); user32.SetForegroundWindow(hwnd)
        user32.AttachThreadInput(ct, ft, False); time.sleep(0.4)
        if user32.GetForegroundWindow() == hwnd: return True
    return False
needle = (sys.argv[1] if len(sys.argv)>1 else "ecomanalytics").lower()
path = sys.argv[2] if len(sys.argv)>2 else os.path.join(os.environ["TEMP"],"opencode","pbi_fg.png")
wins = [(h,t) for h,t in list_windows() if needle in (t or "").lower()]
if not wins:
    print("no window"); sys.exit(2)
hwnd,title = wins[0]
force_focus(hwnd); time.sleep(1.0)
l,t_,r,b = window_rect(hwnd)
from PIL import ImageGrab
img = ImageGrab.grab().crop((l,t_,r,b))
os.makedirs(os.path.dirname(path),exist_ok=True)
img.save(path)
print("saved", path, img.size)
