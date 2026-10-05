"""한글 COM 으로 hwpx 사본을 PDF 로 저장하고 쪽 수를 찍는다. python hwp2pdf.py <hwpx> <pdf>"""

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
