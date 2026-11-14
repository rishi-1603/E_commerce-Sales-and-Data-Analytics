"""Identify rendering visual type names by converting a selected visual via pane icons.

Usage: python hunt_types.py
Loop over row-1 icon coords; for each: select status chart, click icon,
screenshot canvas, Ctrl+S, read the converted visual's visualType.
"""
import ctypes
import glob
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pbi_win2 import find_pbi, force_focus, click_rel, window_rect  # noqa

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

user32 = ctypes.windll.user32
hwnd, _ = find_pbi()
if not hwnd:
    print('NO PBI WINDOW')
    sys.exit(2)
force_focus(hwnd)

PAGES = r'C:\Users\user\portfolio-roadmaps\repos\ecom\powerbi\pbix\EcomAnalytics.Report\definition\pages'
ICONS = [1197, 1238, 1280, 1363]


def save():
    u = user32
    u.SetForegroundWindow(hwnd)
    time.sleep(0.6)
    u.keybd_event(0x11, 0, 0, 0)
    u.keybd_event(0x53, 0, 0, 0)
    u.keybd_event(0x53, 0, 2, 0)
    u.keybd_event(0x11, 0, 2, 0)
    time.sleep(5)


def read_status_visual():
    for vf in glob.glob(os.path.join(PAGES, 'eeb1b7eb*', 'visuals', '*', 'visual.json')):
        v = json.load(open(vf, encoding='utf-8-sig'))
        qs = v['visual'].get('query', {}).get('queryState', {})
        if 'order_status' in json.dumps(qs):
            return v['visual']['visualType']
    return None


results = {}
for ix in ICONS:
    click_rel(hwnd, 670, 380)   # select status chart
    time.sleep(1.2)
    click_rel(hwnd, ix, 424)    # convert via pane icon
    time.sleep(2.5)
    results[ix] = read_status_visual()
    print('icon', ix, '->', results[ix])
    save()

print(json.dumps(results, indent=1))
