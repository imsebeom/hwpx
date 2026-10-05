"""한글 COM 으로 hwpx 사본을 열어 쪽을 매긴 뒤 hwpx 로 다시 저장한다(줄 배치 캐시를 얻으려고). python hwp_resave.py <src> <dst>"""

import sys

import win32com.client as win32

src, out = sys.argv[1], sys.argv[2]
hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")
hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
hwp.XHwpWindows.Item(0).Visible = False
hwp.Open(src, "HWPX", "forceopen:true")
print("pages", hwp.PageCount, flush=True)  # 쪽을 먼저 물어야 조판된 줄 배치가 저장된다
hwp.SaveAs(out, "HWPX", "")
hwp.Clear(1)
hwp.Quit()
print("saved", out)
