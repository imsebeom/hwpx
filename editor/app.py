"""에디터 앱 창: 브리지 서버의 에디터를 WebView2 창(pywebview)으로 띄운다.

브라우저 탭에서는 Ctrl+N, Ctrl+T, Ctrl+W 가 브라우저 예약키라 페이지에 오지 않아 한/글의
Ctrl+N,T(표) Ctrl+N,N(각주) 같은 단축키를 쓸 수 없다. WebView2 에는 새 창·새 탭 단축키가 없고,
pywebview 는 브라우저 단축키(Ctrl+F 찾기, Ctrl+P 인쇄, Ctrl+R 새로 고침 등)도 꺼 둔다.

    python app.py http://localhost:7780/ [창 제목]
"""

import os
import sys

import webview

url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:7780/"
title = sys.argv[2] if len(sys.argv) > 2 else "HWPX 에디터 · Claude"
state = os.environ.get("HWPX_EDITOR_STATE") or os.path.join(
    os.path.expanduser("~"), ".claude", "cache", "hwpx-editor"
)

# 화면보다 큰 고정 크기로 열면 오른쪽 위에 붙는 찾기 창 같은 패널이 화면 밖으로 나간다(2026-09-25 실측). 최대화로 연다.
webview.create_window(title, url, maximized=True, min_size=(900, 600))
# 두 쪽 보기, 확대 비율 같은 에디터 설정(localStorage)이 다음 실행에도 남도록 저장 공간을 고정한다.
webview.start(private_mode=False, storage_path=os.path.join(state, "webview"))
