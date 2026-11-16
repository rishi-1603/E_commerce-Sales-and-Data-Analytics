"""Save the open Power BI report as a .pbix via F12 + UIA dialog driving.

F12 opens Save As in Power BI Desktop. We then drive the common dialog with
programmatic UIA calls (type the filename, click Save, answer confirm/continue
prompts). Exit codes: 0 saved, 4 dialog/edit failure, 5 save never landed.
"""
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

u = ctypes.windll.user32
OUT_PATH = r'C:\Users\user\portfolio-roadmaps\repos\ecom\powerbi\pbix\EcomAnalytics.pbix'

wins = [(h, t) for h, t in list_windows() if 'ecomanalytics' in t.lower()]
if not wins:
    print('NO PBI WINDOW')
    sys.exit(2)
hwnd = wins[0][0]
u.ShowWindow(hwnd, 9)
time.sleep(0.5)
u.SetForegroundWindow(hwnd)
time.sleep(1.2)

# Dismiss stray shell flyouts (battery/volume) that may have stolen focus
VK_ESCAPE = 0x1B
u.keybd_event(VK_ESCAPE, 0, 0, 0)
u.keybd_event(VK_ESCAPE, 0, 2, 0)
time.sleep(1)
u.SetForegroundWindow(hwnd)
time.sleep(0.5)

from pywinauto import Desktop

d = Desktop(backend='uia')


def find_save_dialog():
    """Return a UIA wrapper for the Save As dialog (top-level or owned)."""
    for h, t in list_windows():
        tl = t.lower()
        if 'ecomanalytics' in tl:
            continue
        if 'save' in tl or 'confirm' in tl:
            try:
                return d.window(handle=h)
            except Exception:
                pass
    return None


VK_F12 = 0x7B
if find_save_dialog() is None:
    u.keybd_event(VK_F12, 0, 0, 0)
    u.keybd_event(VK_F12, 0, 2, 0)
    print('pressed F12')
else:
    print('Save As dialog already open')

dlg = None
for attempt in range(10):
    time.sleep(2)
    dlg = find_save_dialog()
    if dlg is not None:
        break
    if attempt == 3:
        print('F12 retry')
        u.SetForegroundWindow(hwnd)
        u.keybd_event(VK_F12, 0, 0, 0)
        u.keybd_event(VK_F12, 0, 2, 0)
if dlg is None:
    print('SAVE DIALOG NOT FOUND; visible windows:')
    for h, t in list_windows():
        print('   ', h, repr(t[:80]))
    sys.exit(4)

print('save dialog found:', dlg.window_text())

# Focus the dialog and switch 'Save as type' to Power BI report (*.pbix)
try:
    dlg.set_focus()
    time.sleep(1)
except Exception as e:
    print('dialog focus failed:', e)

try:
    type_combo = dlg.child_window(title_re='Save as type', control_type='ComboBox')
    type_combo.expand()
    time.sleep(1)
    items = type_combo.descendants(control_type='ListItem')
    texts = [it.window_text() for it in items]
    print('save-as types:', texts)
    match = [it for it in items
             if '.pbix' in (it.window_text() or '').lower()
             and 'pbip' not in (it.window_text() or '').lower()]
    if match:
        try:
            match[0].select()
            print('selected item:', match[0].window_text())
        except Exception:
            match[0].invoke()
            print('invoked item:', match[0].window_text())
    else:
        type_combo.collapse()
    time.sleep(1)
    try:
        type_combo.collapse()
    except Exception:
        pass
    time.sleep(0.5)
except Exception as e:
    print('TYPE SWITCH FAILED:', e)
    sys.exit(4)

try:
    dlg.type_keys('%n', pause=0.3)
    time.sleep(0.5)
    dlg.type_keys('^a{DEL}', pause=0.2)
    dlg.type_keys(OUT_PATH.replace('{', '{{').replace('}', '}}'),
                  pause=0.02, with_spaces=True)
    time.sleep(1.5)
    combo = dlg.child_window(title='File name:', control_type='ComboBox')
    ed = combo.descendants(control_type='Edit')[0]
    try:
        typed = ed.iface_value.CurrentValue
    except Exception:
        typed = ed.window_text()
    print('filename now:', repr(typed))
    if 'ecomanalytics.pbix' not in typed.strip().lower():
        print('TYPED VALUE MISMATCH')
        sys.exit(4)
except Exception as e:
    print('typing failed:', e)
    sys.exit(4)

# Click Save (invoke)
try:
    save_btn = dlg.child_window(title='Save', control_type='Button')
    save_btn.invoke()
    print('clicked Save')
except Exception as e:
    print('save button failed:', e)

# Handle overwrite / continue prompts for up to 45 s
AFFIRM = ('yes', 'continue', 'ok', 'save', 'replace')
deadline = time.time() + 45
while time.time() < deadline:
    time.sleep(3)
    acted = False
    for h, t in list_windows():
        tl = t.lower()
        if 'ecomanalytics' in tl or 'program manager' in tl or 'greeting' in tl:
            continue
        if not tl:
            continue
        try:
            w2 = d.window(handle=h)
            btns = [c for c in w2.descendants(control_type='Button')
                    if (c.window_text() or '').strip().lower() in AFFIRM]
            if btns:
                btns[0].invoke()
                print(f'answered dialog "{t}": {btns[0].window_text()}')
                acted = True
                break
        except Exception:
            pass
    if not acted and os.path.exists(OUT_PATH):
        print('file created:', OUT_PATH)
        break
    if not acted and find_save_dialog() is None:
        # dialog closed; give the model a moment to serialize
        time.sleep(5)
        if os.path.exists(OUT_PATH):
            print('file created after dialog close:', OUT_PATH)
        else:
            print('dialog closed but file missing')
        break

time.sleep(3)
if os.path.exists(OUT_PATH):
    print('SAVED OK —', os.path.getsize(OUT_PATH), 'bytes')
    sys.exit(0)
print('SAVE DID NOT LAND')
sys.exit(5)
