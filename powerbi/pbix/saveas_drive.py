"""Drive the Save As dialog: set name/type, Save, confirm overwrite."""
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

# --- find dialog ---
wins = [(h, t) for h, t in list_windows() if t.strip().lower() == 'save as']
if not wins:
    print('NO SAVE AS DIALOG')
    sys.exit(2)
hwnd = wins[0][0]

from pywinauto import Desktop
d = Desktop(backend='uia')
w = d.window(handle=hwnd)
w.set_focus()
time.sleep(0.8)

# --- save-as type combo ---
combos = [c for c in w.descendants()
          if c.element_info.control_type == 'ComboBox']
type_combo = None
for c in combos:
    if 'pbix' in (c.window_text() or '').lower() or 'power bi' in (c.window_text() or '').lower():
        type_combo = c
        print('type combo current:', repr(c.window_text()))
if type_combo is None:
    for c in combos:
        t = (c.window_text() or '')
        print('combo candidate:', repr(t[:80]))

# --- filename edit ---
edits = [c for c in w.descendants()
         if c.element_info.control_type == 'Edit'
         and c.element_info.rectangle.top > 600]
fn_edit = None
for e in edits:
    try:
        if e.element_info.rectangle.top < 672:
            fn_edit = e
            break
    except Exception:
        pass
if fn_edit is None:
    # fall back: edit inside 'File name:' combo
    for c in combos:
        if 'file name' in (c.element_info.name or '').lower():
            inner = [x for x in c.descendants()
                     if x.element_info.control_type == 'Edit']
            if inner:
                fn_edit = inner[0]
            break

if fn_edit is None:
    print('NO FILENAME EDIT FOUND')
    sys.exit(3)

print('filename edit current:', repr(fn_edit.window_text()))
fn_edit.set_edit_text('EcomAnalytics')
time.sleep(0.5)
print('filename set to:', repr(fn_edit.window_text()))

# --- ensure type is .pbix ---
sel = (type_combo.window_text() or '').lower() if type_combo else ''
if type_combo and ('pbix' not in sel and 'power bi' not in sel):
    print('selecting .pbix type...')
    type_combo.expand()
    time.sleep(0.6)
    items = [i for i in type_combo.descendants()
             if i.element_info.control_type == 'ListItem'
             or i.element_info.control_type == 'ComboBoxItem']
    for i in items:
        nm = (i.element_info.name or '')
        print('  item:', nm)
        if 'pbix' in nm.lower() or 'power bi' in nm.lower():
            i.click_input()
            print('  selected:', nm)
            break
    time.sleep(0.5)

# --- Save ---
save_btns = [b for b in w.descendants()
             if b.element_info.control_type == 'Button'
             and (b.element_info.name or '').strip().replace('&', '') == 'Save']
if not save_btns:
    print('NO SAVE BUTTON')
    sys.exit(4)
save_btns[0].click_input()
print('Save clicked; waiting for possible overwrite confirm...')

# --- overwrite confirm: press Yes if a confirm popup appears ---
time.sleep(2.5)
confirmed = False
for attempt in range(6):
    allw = list_windows()
    for h, t in allw:
        tl = (t or '').lower()
        if t.strip() in ('Save As', 'Confirm Save As') and h != hwnd:
            try:
                wc = d.window(handle=h)
                yes = [b for b in wc.descendants()
                       if b.element_info.control_type == 'Button'
                       and (b.element_info.name or '').strip() in ('Yes', '&Yes')]
                if yes:
                    yes[0].click_input()
                    print('overwrite confirmed (Yes)')
                    confirmed = True
                    break
                texts = [c.window_text() for c in wc.descendants()
                         if (c.window_text() or '').strip()]
                print('popup:', t, texts[:10])
            except Exception as e:
                print('popup err:', e)
    if confirmed:
        break
    time.sleep(1.5)

print('done. overwrite confirmed:', confirmed)
