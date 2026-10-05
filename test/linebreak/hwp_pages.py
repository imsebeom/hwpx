"""한글 COM 으로 문서마다 쪽 수를 잰다(사본에서). python hwp_pages.py <목록.txt> <출력.json>"""

import json
import os
import shutil
import sys
import tempfile

import win32com.client as win32

lst, out = sys.argv[1], sys.argv[2]
files = [line.strip() for line in open(lst, encoding="utf-8") if line.strip()]
tmp = tempfile.mkdtemp(prefix="hwpcnt")
hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")
hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
hwp.XHwpWindows.Item(0).Visible = False
res = {}
for i, f in enumerate(files):
    dst = os.path.join(tmp, f"d{i}.hwpx")
    shutil.copyfile(f, dst)
    try:
        hwp.Open(dst, "HWPX", "forceopen:true")
        res[f] = hwp.PageCount
        hwp.Clear(1)
    except Exception as e:  # noqa: BLE001
        res[f] = str(e)[:100]
hwp.Quit()
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False)
print("done", len(res))
