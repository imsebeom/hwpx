"""에디터 앱 창: 브리지 서버의 에디터를 WebView2 창(pywebview)으로 띄운다.

브라우저 탭에서는 Ctrl+N, Ctrl+T, Ctrl+W 가 브라우저 예약키라 페이지에 오지 않아 한/글의
Ctrl+N,T(표) Ctrl+N,N(각주) 같은 단축키를 쓸 수 없다. WebView2 에는 새 창·새 탭 단축키가 없고,
pywebview 는 브라우저 단축키(Ctrl+F 찾기, Ctrl+P 인쇄, Ctrl+R 새로 고침 등)도 꺼 둔다.

    python app.py http://localhost:7780/ [창 제목]
"""

import json
import os
import sys
import threading
import urllib.request
from urllib.parse import urljoin

import webview

url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:7780/"
title = sys.argv[2] if len(sys.argv) > 2 else "HWPX 에디터 · Claude"
state = os.environ.get("HWPX_EDITOR_STATE") or os.path.join(
    os.path.expanduser("~"), ".claude", "cache", "hwpx-editor"
)


class Api:
    """호스트 페이지(host.js)가 저장 안 한 편집 여부를 알려 온다. 있을 때만 닫기 전에 묻는다."""

    def set_dirty(self, dirty):
        window.confirm_close = bool(dirty)


flushed = False


def on_closing():
    """닫기를 한 번 보류하고 마지막 편집을 기록한 뒤 다시 닫는다.

    closing 은 UI 스레드에서 돌아 여기서 evaluate_js 를 기다리면 멈춘다. 그래서 따로 기록하고 destroy 로 다시 닫는다.
    다시 닫을 때 저장 안 한 편집이 있으면 confirm_close 대화상자가 뜬다.
    """
    global flushed
    if flushed:
        flushed = False
        return None
    threading.Thread(target=flush_then_close, daemon=True).start()
    return False


def flush_then_close():
    global flushed
    result = {}
    done = threading.Event()

    def resolved(value):
        result["r"] = value
        done.set()

    # Promise 는 반환값이 아니라 콜백으로 온다(반환값은 빈 dict)
    threading.Thread(
        target=lambda: window.evaluate_js(
            "window.__claudeFlushForClose ? window.__claudeFlushForClose() : Promise.resolve(null)",
            resolved,
        ),
        daemon=True,
    ).start()
    done.wait(10)  # 기록이 멈춰도 창은 닫힌다
    if isinstance(result.get("r"), dict):
        window.confirm_close = bool(result["r"].get("dirty"))
    flushed = True
    window.destroy()


# 화면보다 큰 고정 크기로 열면 오른쪽 위에 붙는 찾기 창 같은 패널이 화면 밖으로 나간다(2026-09-25 실측). 최대화로 연다.
window = webview.create_window(
    title, url, maximized=True, min_size=(900, 600), js_api=Api()
)
window.events.closing += on_closing
# 두 쪽 보기, 확대 비율 같은 에디터 설정(localStorage)이 다음 실행에도 남도록 저장 공간을 고정한다.
webview.start(
    private_mode=False,
    storage_path=os.path.join(state, "webview"),
    localization={
        "global.quitConfirmation": "저장하지 않은 편집이 있습니다.\n\n"
        "확인을 누르면 저장하지 않고 닫습니다. 저장하려면 취소를 누르고 Ctrl+S 로 저장하세요."
    },
)

# 창이 닫히면 이 창이 붙어 있던 브리지 서버도 내린다(cli stop 과 같은 shutdown). 다시 열 때는 start 가 서버를 새로 띄운다
try:
    urllib.request.urlopen(
        urllib.request.Request(
            urljoin(url, "/api/cmd"),
            data=json.dumps({"type": "shutdown"}).encode(),
            method="POST",
        ),
        timeout=3,
    )
except OSError:
    pass  # 서버가 이미 내려갔다
