"""hancom_layout.py <원본.hwpx> <출력.hwpx>

한글(COM)로 사본을 열어 저장하고, 그 저장본의 줄 배치(linesegarray)와 표 높이(hp:tbl/hp:sz height)만
원본에 옮겨 심는다. 나머지(그림, 서식, 칸 높이)는 원본 그대로다.

왜: 스킬 파이프라인 산출물은 모든 문단에 한 줄짜리 더미 줄 배치를 달고 칸 높이를 한 줄 기준으로 적는다.
rhwp 는 더미를 믿어 한 줄로 누르고, 더미를 걷어도 스스로 잰 줄 수가 그리는 줄 수보다 적어 표가 겹친다.
한글이 계산한 줄 배치와 표 높이를 주면 rhwp 가 한글 재저장본과 글자 좌표까지 같게 그린다(2026-09-26 실측).
한글 재저장본을 통째로 쓰지 않는 것은 그림을 BMP 로 다시 넣어 파일이 부풀기 때문이다.

종료 코드 0 이 아니면 호출자(server.mjs)가 더미만 걷어내는 방식으로 물러난다.
"""

import copy
import os
import shutil
import sys
import tempfile
import zipfile

from lxml import etree

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"


def hancom_resave(src, dst):
    import win32com.client as w

    src, dst = os.path.abspath(src), os.path.abspath(dst)
    hwp = w.gencache.EnsureDispatch("HWPFrame.HwpObject")
    try:
        hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
        if not hwp.Open(src, "HWPX", "forceopen:true"):
            raise RuntimeError("한글이 문서를 열지 못했다")
        # 쪽수를 물어야 끝까지 조판한다. 묻지 않고 저장하면 원래 줄 배치(더미)를 그대로 쓴다(2026-09-26 실측).
        if hwp.PageCount < 1:
            raise RuntimeError("한글이 쪽을 만들지 못했다")
        if not hwp.SaveAs(dst, "HWPX", ""):
            raise RuntimeError("한글이 저장하지 못했다")
    finally:
        hwp.Quit()


def graft(src, laid, out):
    zs, zl = zipfile.ZipFile(src), zipfile.ZipFile(laid)
    names = set(zl.namelist())
    tmp = out + ".tmp"
    with zipfile.ZipFile(tmp, "w") as zo:
        for info in zs.infolist():
            data = zs.read(info)
            if info.filename.startswith("Contents/section") and info.filename in names:
                a = etree.fromstring(data)
                b = etree.fromstring(zl.read(info.filename))
                if any(
                    s.get("horzsize") == "22960" and s.get("flags") == "393216"
                    for s in b.iter(HP + "lineseg")
                ):
                    raise RuntimeError(
                        f"{info.filename} 한글 저장본에 더미 줄 배치가 남았다(조판 전 저장)"
                    )
                pa, pb = list(a.iter(HP + "p")), list(b.iter(HP + "p"))
                ta, tb = list(a.iter(HP + "tbl")), list(b.iter(HP + "tbl"))
                if len(pa) != len(pb) or len(ta) != len(tb):
                    raise RuntimeError(
                        f"{info.filename} 구조가 다르다(문단 {len(pa)}/{len(pb)}, 표 {len(ta)}/{len(tb)})"
                    )
                for x, y in zip(pa, pb):
                    for old in x.findall(HP + "linesegarray"):
                        x.remove(old)
                    new = y.find(HP + "linesegarray")
                    if new is not None:
                        x.append(copy.deepcopy(new))
                for x, y in zip(ta, tb):
                    sx, sy = x.find(HP + "sz"), y.find(HP + "sz")
                    if sx is not None and sy is not None:
                        sx.set("height", sy.get("height"))
                data = etree.tostring(
                    a, xml_declaration=True, encoding="UTF-8", standalone=True
                )
            zo.writestr(info, data)  # 원래 ZipInfo 로 써서 mimetype 무압축을 지킨다
    os.replace(tmp, out)


def main():
    src, out = sys.argv[1], sys.argv[2]
    work = tempfile.mkdtemp(prefix="hwpx-layout-")
    try:
        copy_src = os.path.join(work, "src.hwpx")  # 원본은 한글에 넘기지 않는다
        shutil.copyfile(src, copy_src)
        laid = os.path.join(work, "laid.hwpx")
        hancom_resave(copy_src, laid)
        graft(src, laid, out)
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
