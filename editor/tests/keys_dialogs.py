"""대화상자를 여는 한/글 단축키가 실제로 창을 띄우는지 본다(앱 창, 실제 키 입력).

판정: 키를 누르기 전과 후에 화면에 보이는 짧은 글자(대화상자 제목, 버튼)를 CDP 로 모아 새로 나타난 것을 본다.
rhwp 대화상자는 class 이름이 없고 패널처럼 붙기도 해서 구조로는 못 잡는다(2026-09-25 실측).
그림 넣기(Ctrl+N,I)는 윈도 「열기」 창이 뜨는 것으로 보고 바로 닫는다.
"""

import ctypes
import json
import subprocess
import sys
import time

from keys_app import cli, combo, find_window

sys.stdout.reconfigure(encoding="utf-8")

VISIBLE_TEXTS = (
    "[...new Set([...S.document.querySelectorAll('body *')]"
    ".filter(e => !e.children.length && e.offsetParent && e.textContent.trim() && e.textContent.trim().length < 20)"
    ".map(e => e.textContent.trim()))]"
)


def texts():
    r = subprocess.run(
        ["node", "cdp_eval.mjs", "9333", VISIBLE_TEXTS],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    out = r.stdout.strip()
    return set(json.loads(out)) if out.startswith("[") else set()


def native_open_dialog():
    u = ctypes.WinDLL("user32")
    h = u.FindWindowW("#32770", "열기")
    if h:
        u.PostMessageW(h, 0x0010, 0, 0)  # 시험이 띄운 창이니 닫는다
    return bool(h)


def main():
    # import 만으로 실제 키 입력 시험이 돌지 않게 main 으로 감싼다(2026-09-25 실수로 한 번 돌았다)
    hwnd = find_window()
    cases = [
        ("Ctrl+N,T 표 만들기", [("CTRL", "N"), ("T",)]),
        ("Ctrl+Q,A 찾아 바꾸기", [("CTRL", "Q"), ("A",)]),
        ("Ctrl+H 찾아 바꾸기", [("CTRL", "H")]),
        ("Ctrl+Q,F 찾기", [("CTRL", "Q"), ("F",)]),
        ("Ctrl+N,G 구역 설정", [("CTRL", "N"), ("G",)]),
        ("Ctrl+N,B 글상자", [("CTRL", "N"), ("B",)]),
        ("Ctrl+F10 문자표", [("CTRL", "F10")]),
        ("Ctrl+N,I 그림", [("CTRL", "N"), ("I",)]),
    ]
    for name, keys in cases:
        cli("goto", "p6")
        combo(hwnd, "END")
        before = texts()
        for k in keys:
            combo(hwnd, *k)
        time.sleep(1.0)
        if "그림" in name:
            print(
                f"{name:<22} → {'윈도 열기 창 뜸(닫음)' if native_open_dialog() else '안 뜸'}"
            )
            time.sleep(0.5)
            continue
        new = sorted(texts() - before)
        print(f"{name:<22} → {new[:8] or '새로 보이는 것 없음'}")
        combo(hwnd, "ESC")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
