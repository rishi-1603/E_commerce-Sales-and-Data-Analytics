"""Capture the full screen (or a named window) to a PNG."""
import sys
from pywinauto import Desktop
from pywinauto.application import Application


def shot_screen(path):
    import pywinauto
    d = Desktop(backend='uia')
    # capture whole virtual screen via the desktop window
    dlg = d.window(handle=pywinauto.findwindows.get_desktop_element().handle) if False else None
    # simpler: use PIL ImageGrab
    from PIL import ImageGrab
    img = ImageGrab.grab(all_screens=True)
    img.save(path)
    print('saved', path, img.size)


def shot_window(title_substr, path):
    d = Desktop(backend='uia')
    wins = [w for w in d.windows() if title_substr.lower() in (w.window_text() or '').lower()]
    if not wins:
        print('NO WINDOW matching', title_substr)
        sys.exit(2)
    w = wins[0]
    w.set_focus()
    img = w.capture_as_image()
    img.save(path)
    print('saved', path, img.size, '| title:', w.window_text())


if __name__ == '__main__':
    mode = sys.argv[1]
    path = sys.argv[2]
    if mode == 'screen':
        shot_screen(path)
    else:
        shot_window(sys.argv[3] if len(sys.argv) > 3 else 'Power BI', path)
