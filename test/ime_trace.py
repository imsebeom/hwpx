"""한글 입력기 상태에서 Ctrl+M,R 을 누를 때 키, 조합, 입력 이벤트 순서를 앱 창에서 기록한다(진단용).

앱 창은 WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=9333 으로 떠 있어야 한다.
"""

import subprocess
import sys

from keys_app import VK, cli, combo, ensure_front, find_window, send_vk

sys.stdout.reconfigure(encoding="utf-8")


def cdp(expr):
    r = subprocess.run(
        ["node", "cdp_eval.mjs", "9333", expr],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return r.stdout.strip()


TRACE = """(() => {
  const S2 = S; S2.__t = [];
  const g = () => { try { return S2.document.querySelector('textarea') && 'x'; } catch { return '?'; } };
  const log = (e) => S2.__t.push([e.type, e.key ?? '', e.code ?? '', e.keyCode ?? '', e.isComposing ?? '', e.data ?? '', e.inputType ?? '', e.defaultPrevented]);
  for (const t of ['keydown', 'compositionstart', 'compositionupdate', 'compositionend', 'beforeinput', 'input'])
    S2.addEventListener(t, log, true);
  return 'ok';
})()"""

hwnd = find_window()
print(cdp(TRACE))
cli("goto", "p4")
ensure_front(hwnd)
send_vk(VK["HANGUL"])
combo(hwnd, "CTRL", "M")
combo(hwnd, "R")
send_vk(VK["HANGUL"])
print(cdp("S.__t"))
print(cli("text").splitlines()[4:6])
