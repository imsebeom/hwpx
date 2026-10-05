"""한글 COM 하나로 여러 hwpx 를 열어 쪽을 매긴 뒤 <이름>_hwp.hwpx 로 다시 저장한다. python hwp_resave_many.py <파일...>"""

import sys

import win32com.client as win32

hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")
hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
hwp.XHwpWindows.Item(0).Visible = False
for src in sys.argv[1:]:
    out = src[: -len(".hwpx")] + "_hwp.hwpx"
    hwp.Open(src, "HWPX", "forceopen:true")
    print(src.rsplit("\\", 1)[-1], "pages", hwp.PageCount, flush=True)
    hwp.SaveAs(out, "HWPX", "")
    hwp.Clear(1)
hwp.Quit()
