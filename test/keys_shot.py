"""단축키를 누른 직후 앱 창을 캡처한다(진단용).  python keys_shot.py CTRL+N T  → keys_shot.png"""

import ctypes
import sys
import time
from ctypes import wintypes

from keys_app import cli, combo, find_window, user32
from PIL import ImageGrab

hwnd = find_window()
cli("goto", "p6")
combo(hwnd, "END")
for step in sys.argv[1:]:
    combo(hwnd, *step.split("+"))
time.sleep(0.8)
r = wintypes.RECT()
user32.GetWindowRect(hwnd, ctypes.byref(r))
img = ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom), all_screens=True)
img.thumbnail((1100, 1100))
img.save("keys_shot.png")
combo(hwnd, "ESC")
print("saved", img.size)
