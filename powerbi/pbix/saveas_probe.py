"""Inspect and drive the Power BI Save As dialog via UIA."""
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

wins = [(h, t) for h, t in list_windows() if t.strip().lower() == 'save as']
if not wins:
    print('NO SAVE AS DIALOG')
    sys.exit(2)
hwnd = wins[0][0]
print('dialog hwnd:', hwnd)

from pywinauto import Desktop
d = Desktop(backend='uia')
w = d.window(handle=hwnd)

print('--- filename edit ---')
edits = [c for c in w.descendants()
         if c.element_info.control_type == 'Edit']
for e in edits[:6]:
    print('edit:', repr(e.window_text()), e.element_info.rectangle)

print('--- file type combo ---')
for c in w.descendants():
    if c.element_info.control_type == 'ComboBox':
        print('combo:', repr(c.window_text()[:60]), c.element_info.rectangle)

print('--- buttons ---')
for c in w.descendants():
    if c.element_info.control_type == 'Button':
        nm = (c.window_text() or '').strip()
        if nm and len(nm) < 40:
            print('btn:', nm, c.element_info.rectangle)

print('--- toolbar / address ---')
for c in w.descendants():
    nm = (c.element_info.name or '')
    if 'address' in nm.lower() or 'Toolbar' in c.element_info.control_type:
        print('ctrl:', c.element_info.control_type, repr(nm[:80]))
