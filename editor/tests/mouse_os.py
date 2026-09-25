"""운영체제 실제 마우스로 표 선을 누른다. CDP 로 CSS 좌표를 구하고 창 클라이언트 원점과 배율로 화면 좌표로 바꾼다.

사용: python os_mouse.py <ppi> <top|inner|cell> <흔들림px> [drag] — drag 면 25px 끈다.
"""

import ctypes
import json
import subprocess
import sys
import time
from ctypes import wintypes

sys.stdout.reconfigure(encoding="utf-8")
ctypes.windll.shcore.SetProcessDpiAwareness(2)
user32 = ctypes.windll.user32
EVAL = r"C:/Users/hccga/.claude/skills/hwpx/editor/tests/cdp_eval.mjs"
ppi, where, wob = int(sys.argv[1]), sys.argv[2], int(sys.argv[3])
drag = len(sys.argv) > 4


def ev(expr):
    out = subprocess.run(
        ["node", EVAL, "9333", expr], capture_output=True, text=True, encoding="utf-8"
    ).stdout.strip()
    return json.loads(json.loads(out)) if out.startswith('"') else json.loads(out)


# 창 찾기
found = []


@ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
def _enum(h, _):
    buf = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(h, buf, 256)
    if buf.value.startswith("HWPX 에디터") and user32.IsWindowVisible(h):
        found.append(h)
    return True


user32.EnumWindows(_enum, 0)
hwnd = found[0]
user32.ShowWindow(hwnd, 9)
user32.SetForegroundWindow(hwnd)
time.sleep(0.3)

y_expr = {"top": "tb.y", "inner": "bb[0].y + bb[0].h", "cell": "bb[0].y + bb[0].h / 2"}[
    where
]
pt = ev(f"""(async () => {{
  const ih = S.__claudeIH(); const w = ih.wasm;
  const bb = w.getTableCellBboxes(0, {ppi}, 0); const page = bb[0].pageIndex ?? 0;
  const tb = w.getTableBBoxAtPage(0, {ppi}, 0, page);
  const y0 = {y_expr};
  const sc = S.document.querySelector('#scroll-content'); const zoom = ih.viewportManager.getZoom();
  ih.container.scrollTop = ih.virtualScroll.getPageOffset(page) + y0 * zoom - 200;
  await new Promise(r => setTimeout(r, 400));
  const F = document.querySelector('iframe').getBoundingClientRect();
  const rect = sc.getBoundingClientRect(); const left = ih.virtualScroll.getPageLeftResolved(page, sc.clientWidth);
  return JSON.stringify({{ x: F.left + rect.left + left + (tb.x + tb.width / 2) * zoom,
    y: F.top + rect.top + ih.virtualScroll.getPageOffset(page) + y0 * zoom, dpr: window.devicePixelRatio }});
}})()""")
origin = wintypes.POINT(0, 0)
user32.ClientToScreen(hwnd, ctypes.byref(origin))
sx = int(origin.x + pt["x"] * pt["dpr"])
sy = int(origin.y + pt["y"] * pt["dpr"])

LEFTDOWN, LEFTUP = 0x0002, 0x0004
for k in (40, 20, 8, 0):  # 표 안으로 들어가며 다가간다
    user32.SetCursorPos(sx + k, sy + k)
    time.sleep(0.12)
user32.mouse_event(LEFTDOWN, 0, 0, 0, 0)
time.sleep(0.08)
dy = 25 * int(pt["dpr"]) if drag else wob
user32.SetCursorPos(sx, sy + dy)
time.sleep(0.08)
user32.mouse_event(LEFTUP, 0, 0, 0, 0)
time.sleep(0.4)
st = ev(
    "(() => { const ih = S.__claudeIH(); return JSON.stringify({ obj: ih.cursor.isInTableObjectSelection(), ref: ih.cursor.selectedTableRef, pos: ih.getCursorPosition() }); })()"
)
print(where, "흔들림" if not drag else "드래그", dy, "→", st)
