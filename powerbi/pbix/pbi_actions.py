"""Expand Fact_Orders in Data pane + click Home ribbon Refresh, via click_input."""
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

wins = [(h, t) for h, t in list_windows() if 'ecomanalytics' in t.lower()]
if not wins:
    print('NO PBI WINDOW')
    sys.exit(2)
hwnd = wins[0][0]

for h, t in list_windows():
    tl = t.lower()
    if any(k in tl for k in ('power bi', 'ecomanalytics', 'program manager', 'greeting')):
        continue
    user32.ShowWindow(h, 6)
time.sleep(0.5)

from pywinauto import Desktop
d = Desktop(backend='uia')
w = d.window(handle=hwnd)

mode = sys.argv[1] if len(sys.argv) > 1 else 'expand'

if mode == 'refresh':
    # Home ribbon Refresh button (big circular arrows)
    btns = [c for c in w.descendants()
            if c.element_info.control_type == 'Button'
            and (c.element_info.name or '').strip() == 'Refresh']
    print('ribbon Refresh buttons:', len(btns))
    for b in btns[:3]:
        r = b.element_info.rectangle
        print('  rect:', r.left, r.top, r.right, r.bottom)
    if btns:
        btns[0].click_input()
        print('clicked ribbon Refresh')

elif mode == 'expand':
    # tree items in Data pane
    items = [c for c in w.descendants()
             if c.element_info.control_type in ('TreeItem', 'ListItem', 'DataItem')
             and (c.element_info.name or '').strip() == 'Fact_Orders']
    print('Fact_Orders items:', len(items))
    for it in items:
        r = it.element_info.rectangle
        print('  rect:', r.left, r.top, r.right, r.bottom, '| expandable:', it.element_info.framework_id if hasattr(it.element_info, 'framework_id') else '')
    if items:
        items[0].click_input(double_click=True)
        print('double-clicked Fact_Orders')
