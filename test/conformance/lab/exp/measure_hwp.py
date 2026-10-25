"""변형 hwpx를 한글로 열어 측정하고 HWPX로 다시 저장한다. hidden_desktop.py 안에서 돌린다.

측정: Open 반환값, hwp.Path, 쪽수, 본문 텍스트, 쪽별 텍스트, 뜬 대화상자 제목
사용: python measure.py <변형 폴더> <재저장 폴더> <결과.json>
"""

import glob
import json
import os
import sys

import pythoncom
import win32com.client as win32

# 대화상자 감시기(probe_defaults.Watchdog)가 든 폴더. 비공개 저장소라 공개 코드에 경로를 적지 않고 환경 변수로 받는다
_probe = os.environ.get("HWP_PROBE_SCRIPTS")
if not _probe:
    sys.exit("환경 변수 HWP_PROBE_SCRIPTS 에 probe_defaults.py 가 든 폴더를 지정하세요")
sys.path.insert(0, _probe)
from probe_defaults import Watchdog

sys.stdout.reconfigure(encoding="utf-8")


def main(src_dir, rt_dir, dst):
    os.makedirs(rt_dir, exist_ok=True)
    pythoncom.CoInitialize()
    hwp = win32.DispatchEx("HWPFrame.HwpObject")
    hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
    hwp.SetMessageBoxMode(0x00020000)
    wd = Watchdog()
    wd.start()
    res = {}
    try:
        for f in sorted(glob.glob(os.path.join(src_dir, "*.hwp"))):
            name = os.path.splitext(os.path.basename(f))[0]
            rec = {}
            wd.begin()
            try:
                rec["open"] = bool(
                    hwp.Open(os.path.abspath(f), "HWP", "forceopen:true")
                )
                rec["path"] = hwp.Path
                rec["pages"] = hwp.PageCount
                rec["text"] = hwp.GetTextFile("TEXT", "")
                # 쪽별 텍스트는 GetPageText가 표를 시작 쪽에 통째로 돌려줘 못 믿는다. PDF 렌더로 잰다.
                pdf = os.path.abspath(os.path.join(rt_dir, name + ".pdf"))
                rec["pdf"] = bool(hwp.SaveAs(pdf, "PDF", ""))
                out = os.path.abspath(os.path.join(rt_dir, name + ".hwpx"))
                rec["resaved"] = bool(hwp.SaveAs(out, "HWPX", ""))
            except pythoncom.com_error as e:
                rec["error"] = str(e.args[1])
            dialogs = wd.end()
            if dialogs:
                rec["dialog"] = dialogs
            hwp.Clear(1)
            res[name] = rec
            print(
                name,
                rec.get("open"),
                rec.get("pages"),
                rec.get("error", ""),
                dialogs or "",
                flush=True,
            )
    finally:
        with open(dst, "w", encoding="utf-8") as fp:
            json.dump(res, fp, ensure_ascii=False, indent=1)
        hwp.Quit()


if __name__ == "__main__":
    main(*sys.argv[1:4])
