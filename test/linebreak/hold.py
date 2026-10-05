"""보이지 않는 크로미움으로 시험 에디터를 열어 두고 CDP 포트(9333)를 연다. 15분 뒤 닫는다."""

import sys
import time

from playwright.sync_api import sync_playwright

port = sys.argv[1] if len(sys.argv) > 1 else "7780"
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--remote-debugging-port=9333"])
    pg = b.new_page(viewport={"width": 1400, "height": 1000})
    pg.goto(f"http://localhost:{port}/")
    print("opened", flush=True)
    time.sleep(3600)
    b.close()
