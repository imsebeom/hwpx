"""키를 하나씩 보내며 커서와 선택 상태를 찍는다(진단용). keys_app.py 의 함수를 빌려 쓴다."""

import sys

from keys_app import VK, cli, combo, cursor, ensure_front, find_window, send_vk

sys.stdout.reconfigure(encoding="utf-8")


def show(label):
    c = cursor()
    at = c["cell"]["ref"] if c.get("cell") else f"p{c['para']}:{c['charOffset']}"
    print(f"{label:<22} 커서 {at:<10} 선택 {c.get('selectedText')!r}")


hwnd = find_window()
if "--hangul" in sys.argv:
    ensure_front(hwnd)
    send_vk(VK["HANGUL"])
for ref in ("T1r2c1", "p6"):
    cli("goto", ref)
    show(f"goto {ref}")
    combo(hwnd, "END")
    show("  End")
    combo(hwnd, "CTRL", "A")
    show("  Ctrl+A")

if "--hangul" in sys.argv:
    ensure_front(hwnd)
    send_vk(VK["HANGUL"])
