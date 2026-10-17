"""한글 정답본 만들기(작업자). 숨은 데스크톱 안에서 돈다. oracle_driver.py 가 부른다.

목록의 사본마다: 한글로 열고(Open 반환값과 Path 확인) → 쪽수를 먼저 묻고(그래야 조판된 줄 기록이 남는다)
→ HWPX 로 다시 저장한다. 결과는 문서마다 json 한 줄로 바로 쓴다.
대화상자가 STALL 초를 넘기면 감시 스레드가 이 데스크톱의 보이는 창(문서 창 제외)을 닫는다.

    python oracle_worker.py <목록.tsv(id\\t사본경로)> <정답 폴더> <결과.jsonl>
"""

import ctypes
import ctypes.wintypes as wt
import json
import os
import sys
import threading
import time

import pythoncom
import win32com.client as win32

sys.stdout.reconfigure(encoding="utf-8")
STALL = 8
u32 = ctypes.windll.user32


def close_dialogs(desk):
    closed = []
    proc = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

    def cb(hwnd, _):
        if not u32.IsWindowVisible(hwnd):
            return True
        buf = ctypes.create_unicode_buffer(256)
        u32.GetWindowTextW(hwnd, buf, 256)
        if buf.value.endswith(" - 한글"):
            return True
        closed.append(buf.value)
        u32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
        return True

    u32.EnumDesktopWindows(desk, proc(cb), 0)
    return closed


class Watchdog(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.desk = u32.GetThreadDesktop(ctypes.windll.kernel32.GetCurrentThreadId())
        self.started, self.closed, self.lock = None, [], threading.Lock()

    def begin(self):
        with self.lock:
            self.started, self.closed = time.time(), []

    def end(self):
        with self.lock:
            self.started = None
            return self.closed

    def run(self):
        while True:
            time.sleep(1)
            with self.lock:
                if self.started and time.time() - self.started > STALL:
                    self.closed += close_dialogs(self.desk)
                    self.started = time.time()


def main(lst, out_dir, res_path):
    items = [
        line.rstrip("\n").split("\t")
        for line in open(lst, encoding="utf-8")
        if line.strip()
    ]
    pythoncom.CoInitialize()
    hwp = win32.DispatchEx("HWPFrame.HwpObject")
    hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
    hwp.SetMessageBoxMode(0x00020000)
    wd = Watchdog()
    wd.start()
    out = open(res_path, "a", encoding="utf-8", buffering=1)
    try:
        for did, src in items:
            rec = {"id": did}
            wd.begin()
            t0 = time.time()
            try:
                fmt = "HWP" if src.lower().endswith(".hwp") else "HWPX"
                ok = bool(hwp.Open(os.path.abspath(src), fmt, "forceopen:true"))
                rec["open"] = ok and bool(hwp.Path)
                if rec["open"]:
                    rec["pages"] = hwp.PageCount
                    dst = os.path.abspath(os.path.join(out_dir, did + ".hwpx"))
                    rec["saved"] = bool(hwp.SaveAs(dst, "HWPX", ""))
            except pythoncom.com_error as e:
                rec["error"] = str(e.args[1])
            dialogs = wd.end()
            if dialogs:
                rec["dialog"] = dialogs
            rec["sec"] = round(time.time() - t0, 1)
            try:
                hwp.Clear(1)
            except pythoncom.com_error:
                pass
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
    finally:
        hwp.Quit()


if __name__ == "__main__":
    main(*sys.argv[1:4])
