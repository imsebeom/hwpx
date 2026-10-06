"""보이지 않는 크로미움으로 시험 에디터를 열어 두고 CDP 포트(9333)를 연다. 15분 뒤 닫는다.

포트는 `cli.mjs list` 로 확인한 시험 인스턴스 것을 준다. 그 서버에 이미 창이 붙어 있으면(사용자 창일 수 있다)
열지 않고 끝난다 — 2026-10-06 에 7781 시험 인스턴스를 두고 기본값 7780(사용자 창)에 붙을 뻔했다.
"""

import json
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright

port = sys.argv[1] if len(sys.argv) > 1 else "7780"
try:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=2) as r:
        health = json.load(r)
except Exception as e:  # noqa: BLE001
    sys.exit(
        f"포트 {port} 에 에디터 서버가 없다({e}). `node cli.mjs list` 로 시험 인스턴스 포트를 확인한다"
    )
if health.get("browser"):
    sys.exit(
        f"포트 {port} 서버에는 이미 창이 붙어 있다(사용자 창일 수 있다). `start --no-browser` 로 띄운 시험 인스턴스 포트를 준다"
    )
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--remote-debugging-port=9333"])
    pg = b.new_page(viewport={"width": 1400, "height": 1000})
    pg.goto(f"http://localhost:{port}/")
    print("opened", flush=True)
    time.sleep(3600)
    b.close()
