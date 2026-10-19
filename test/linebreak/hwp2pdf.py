"""한글 COM 으로 hwpx 사본을 PDF 로 저장하고 쪽 수를 찍는다. python hwp2pdf.py <hwpx> <pdf>

⚠ 줄 배치(linesegarray)를 지운 사본은 「pages 1」만 찍고 PDF 를 남기지 않는다(2026-10-20) — 그런 사본은 REA/hwp2024/hwpx_lab/measure.py 로 잰다.
"""

import sys

import win32com.client as win32

src, out = sys.argv[1], sys.argv[2]
hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")
hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
hwp.XHwpWindows.Item(0).Visible = False
hwp.Open(src, "HWPX", "forceopen:true")
print("pages", hwp.PageCount, flush=True)
hwp.SaveAs(out, "PDF", "")
hwp.Clear(1)
hwp.Quit()
print("saved", out)
