"""에디터 앱 창에 운영체제 수준 키 입력(SendInput)을 보내 한/글 단축키를 실측한다.

Playwright 의 키 입력은 브라우저 예약키 처리를 거치지 않아 Ctrl+N 이 페이지에 오는지 알 수 없다.
그래서 실제 키보드와 같은 경로(SendInput)로 보낸다. 키를 보내기 직전마다 맨 앞 창이 시험 창인지
확인하고, 아니면 멈춘다(다른 창에 글자가 들어가지 않게).

    HWPX_EDITOR_PORT=7781 HWPX_EDITOR_STATE=... python editor/tests/keys_app.py [--hangul]
"""

import ctypes
import json
import os
import subprocess
import sys
import time
from ctypes import wintypes

sys.stdout.reconfigure(encoding="utf-8")
user32 = ctypes.WinDLL("user32", use_last_error=True)
TITLE = "HWPX 에디터 · Claude"
CLI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cli.mjs")

VK = {
    "CTRL": 0x11,
    "SHIFT": 0x10,
    "ALT": 0x12,
    "END": 0x23,
    "HANGUL": 0x15,
    "ESC": 0x1B, "F10": 0x79,
}
KEYEVENTF_KEYUP = 0x0002


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class INPUT(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT), ("pad", ctypes.c_byte * 32)]

    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _U)]


def find_window():
    return user32.FindWindowW(None, TITLE)


def ensure_front(hwnd):
    if user32.GetForegroundWindow() != hwnd:
        # 포그라운드 잠금을 풀려고 ALT 를 한 번 눌렀다 뗀 뒤 앞으로 가져온다
        send_vk(VK["ALT"])
        user32.ShowWindow(hwnd, 9)
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.4)
    if user32.GetForegroundWindow() != hwnd:
        sys.exit(
            "중단: 시험 창이 맨 앞에 오지 않았다(다른 창에 키가 가지 않도록 멈춘다)"
        )


def send(inputs):
    arr = (INPUT * len(inputs))(*inputs)
    user32.SendInput(len(inputs), arr, ctypes.sizeof(INPUT))


EXTENDED = {
    0x23,
    0x24,
    0x2D,
    0x2E,
    0x25,
    0x26,
    0x27,
    0x28,
}  # End Home Insert Delete 방향키


def key(vk, up=False):
    # 실제 키보드처럼 스캔 코드를 함께 보낸다. 없으면 브라우저의 e.code 가 빈 값이 된다(2026-09-25 실측).
    i = INPUT()
    i.type = 1
    flags = (KEYEVENTF_KEYUP if up else 0) | (0x0001 if vk in EXTENDED else 0)
    i.ki = KEYBDINPUT(vk, user32.MapVirtualKeyW(vk, 0), flags, 0, 0)
    return i


def send_vk(vk):
    send([key(vk), key(vk, True)])


def combo(hwnd, *vks):
    """combo(hwnd, CTRL, 'N') — 앞의 것들을 누른 채 마지막을 누른다."""
    ensure_front(hwnd)
    codes = [VK[v] if v in VK else ord(v) for v in vks]
    send([key(c) for c in codes] + [key(c, True) for c in reversed(codes)])
    time.sleep(0.35)


def cli(*args, stdin=None):
    r = subprocess.run(
        ["node", CLI, *args],
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if args and args[0] == "goto":
        time.sleep(0.3)  # 에디터가 커서를 옮기고 포커스를 가져갈 시간
    return r.stdout.strip()


def cursor():
    return json.loads(cli("state"))["cursor"]


def controls(kind):
    ops = json.dumps([{"doc": "getControls", "a": []}])
    return sum(
        1 for c in json.loads(cli("run", "-", stdin=ops))[0] if c.get("ctrlId") == kind
    )


def main():
    hwnd = find_window()
    if not hwnd:
        sys.exit("시험 창을 못 찾았다")
    results = []

    if "--hangul" in sys.argv:
        ensure_front(hwnd)
        send_vk(VK["HANGUL"])  # 한/영 전환: 한글 입력기 상태에서 같은 시험을 한다
        time.sleep(0.3)

    # 1) 셀 안 Ctrl+A → 그 셀 글 전체
    cli("goto", "T1r2c1")
    combo(hwnd, "END")
    combo(hwnd, "CTRL", "A")
    sel = cursor().get("selectedText")
    results.append(("셀 안 Ctrl+A", sel == "시립 박물관", repr(sel)))

    # 2) 본문 Ctrl+A → rhwp 기본(문서 전체) 유지
    cli("goto", "p6")
    combo(hwnd, "END")
    combo(hwnd, "CTRL", "A")
    sel = cursor().get("selectedText") or ""
    results.append(
        ("본문 Ctrl+A(문서 전체)", "준비물" in sel and "가을" in sel, f"{len(sel)}자")
    )

    # 3) Ctrl+N,N → 각주
    cli("goto", "p6")
    combo(hwnd, "END")
    before = controls("fn")
    combo(hwnd, "CTRL", "N")
    combo(hwnd, "N")
    time.sleep(0.6)
    after = controls("fn")
    results.append(("Ctrl+N,N 각주", after == before + 1, f"각주 {before}→{after}"))
    combo(hwnd, "ESC")  # 각주 편집에서 본문으로

    # 4) Ctrl+M,R → 빨간 글자 (문단 선택 후)
    cli("goto", "p6")
    combo(hwnd, "CTRL", "M")
    combo(hwnd, "R")
    time.sleep(0.4)
    props = json.loads(
        cli("run", "-", stdin=json.dumps([{"doc": "getCharPropertiesAt", "a": [0, 6, 2]}]))
    )[0]
    color = props.get("textColor") if isinstance(props, dict) else props
    results.append(
        ("Ctrl+M,R 빨강", str(color).upper() in ("#FF0000", "#FFFF0000"), str(color))
    )

    # 5) Ctrl+Shift+C → 가운데 정렬 (브라우저에서는 개발자 도구 키)
    cli("goto", "p6")
    combo(hwnd, "END")
    combo(hwnd, "CTRL", "SHIFT", "C")
    para = json.loads(
        cli("run", "-", stdin=json.dumps([{"doc": "getParaPropertiesAt", "a": [0, 6]}]))
    )[0]
    results.append(
        (
            "Ctrl+Shift+C 가운데",
            str(para.get("alignment")).lower() == "center",
            str(para.get("alignment")),
        )
    )

    # 6) 입력기 글자가 새어 들어가 본문을 덮어쓰지 않았는가
    text = cli("text")
    results.append(("본문 보존(입력기 글자 새지 않음)", "학생들이 지역 박물관" in text and "시립 박물관" in text, f"{len(text)}자"))

    if "--hangul" in sys.argv:
        ensure_front(hwnd)
        send_vk(VK["HANGUL"])  # 원래 입력기 상태로

    for name, ok, detail in results:
        print(f"{'통과' if ok else '실패'}  {name}  ({detail})")


if __name__ == "__main__":
    main()
