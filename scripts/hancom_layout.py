"""hancom_layout.py <원본.hwpx> [<출력.hwpx>]  — 출력을 빼면 원본을 고친다.

한글(COM)로 사본을 열어 저장하고, 그 저장본의 줄 배치(linesegarray)와 표 높이(hp:tbl/hp:sz height)만
원본에 옮겨 심는다. 나머지(그림, 서식, 칸 높이)는 원본 그대로다.

왜: 스킬이 XML 을 직접 조립하면 줄 배치를 계산할 수 없어 한 줄짜리 더미(hwpx_helpers.LINESEG_DUMMY)를 넣고
칸 높이를 한 줄 기준으로 적는다. 한글은 열 때 다시 조판하지만 rhwp 같은 다른 구현체는 더미를 믿어 문단을
한 줄로 누르고, 더미를 걷어도 글자처럼 취급하는 표의 행을 늘리지 못해 아래 표와 겹친다(rhwp 결함).
한글이 계산한 줄 배치와 표 높이를 넣으면 rhwp 가 한글 재저장본과 글자 좌표까지 같게 그린다(2026-09-26 실측).
한글 재저장본을 통째로 쓰지 않는 것은 그림을 BMP 로 다시 넣어 파일이 부풀기 때문이다.

fix_namespaces.py 가 마지막 단계에서 부른다. 한글이 없거나 실패하면 LayoutError 를 내고 파일은 그대로 둔다.
"""

import copy
import os
import shutil
import sys
import tempfile
import time
import zipfile

from lxml import etree

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
LOCK = os.path.join(tempfile.gettempdir(), "hwpx-hancom-layout.lock")


class LayoutError(RuntimeError):
    pass


def _acquire_lock(timeout=180):
    """한글 COM 을 한 번에 하나만 쓴다. 병렬 빌드가 동시에 부르면 인스턴스끼리 충돌한다."""
    start = time.time()
    while True:
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return
        except FileExistsError:
            try:
                if (
                    time.time() - os.path.getmtime(LOCK) > 300
                ):  # 죽은 프로세스가 남긴 잠금
                    os.remove(LOCK)
                    continue
            except OSError:
                pass
            if time.time() - start > timeout:
                raise LayoutError("다른 한글 조판 작업이 끝나지 않는다(잠금 대기 초과)")
            time.sleep(0.5)


def hancom_resave(src, dst):
    try:
        import win32com.client as w
    except ImportError as e:
        raise LayoutError("pywin32 가 없다(한글 COM 불가)") from e
    src, dst = os.path.abspath(src), os.path.abspath(dst)
    _acquire_lock()
    try:
        # 앞 작업이 닫는 중인 한글에 붙으면 띄우기나 작업 도중에 RPC 오류가 난다(2026-09-26 동시 실행 실측).
        # 띄우기부터 저장까지를 통째로 다시 시도한다.
        last = None
        for _ in range(3):
            try:
                _resave_once(w, src, dst)
                return
            except Exception as e:  # COM 오류 종류가 여럿이라 모두 다시 시도한다
                last = e
                time.sleep(2)
        raise LayoutError(f"한글 조판 실패: {last}") from last
    finally:
        time.sleep(1)  # 한글이 완전히 닫힌 뒤 다음 작업이 띄우게 한다
        try:
            os.remove(LOCK)
        except OSError:
            pass


def _resave_once(w, src, dst):
    if os.path.exists(dst):
        os.remove(dst)
    hwp = w.gencache.EnsureDispatch("HWPFrame.HwpObject")
    try:
        hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
        if not hwp.Open(src, "HWPX", "forceopen:true"):
            raise LayoutError("한글이 문서를 열지 못했다")
        # 쪽수를 물어야 끝까지 조판한다. 묻지 않고 저장하면 원래 줄 배치를 그대로 쓴다(2026-09-26 실측).
        if hwp.PageCount < 1:
            raise LayoutError("한글이 쪽을 만들지 못했다")
        if not hwp.SaveAs(dst, "HWPX", "") or not os.path.exists(dst):
            raise LayoutError("한글이 저장하지 못했다")
    finally:
        try:
            hwp.Quit()
        except Exception:
            pass  # 저장까지 끝났으면 닫기 실패는 결과에 영향이 없다


def _segs(root):
    return [etree.tostring(x) for x in root.iter(HP + "linesegarray")]


def _has_dummy(root):
    """hwpx_helpers.LINESEG_DUMMY 모양의 줄 배치가 있는가. 이미 한글 줄 배치가 든 문서는 결과가 같아도 정상이다."""
    return any(
        s.get("horzsize") == "22960"
        and s.get("flags") == "393216"
        and s.get("vertsize") == "900"
        for s in root.iter(HP + "lineseg")
    )


def graft(src, laid, out):
    zs, zl = zipfile.ZipFile(src), zipfile.ZipFile(laid)
    names = set(zl.namelist())
    parts = {}
    for info in zs.infolist():
        if not (
            info.filename.startswith("Contents/section") and info.filename in names
        ):
            continue
        a = etree.fromstring(zs.read(info))
        b = etree.fromstring(zl.read(info.filename))
        pa, pb = list(a.iter(HP + "p")), list(b.iter(HP + "p"))
        ta, tb = list(a.iter(HP + "tbl")), list(b.iter(HP + "tbl"))
        if len(pa) != len(pb) or len(ta) != len(tb):
            raise LayoutError(
                f"{info.filename} 구조가 다르다(문단 {len(pa)}/{len(pb)}, 표 {len(ta)}/{len(tb)})"
            )
        if _has_dummy(a) and _segs(a) == _segs(b):
            raise LayoutError(
                f"{info.filename} 한글 저장본의 줄 배치가 원본과 같다(조판 전 저장)"
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
        parts[info.filename] = etree.tostring(
            a, xml_declaration=True, encoding="UTF-8", standalone=True
        )
    zs.close()
    zl.close()
    tmp = out + ".tmp"
    with zipfile.ZipFile(src) as zs, zipfile.ZipFile(tmp, "w") as zo:
        for info in zs.infolist():  # 원래 ZipInfo 로 써서 mimetype 무압축을 지킨다
            zo.writestr(info, parts.get(info.filename, zs.read(info)))
    os.replace(tmp, out)


def apply_hancom_layout(src, out=None):
    """src 에 한글 줄 배치를 옮겨 심어 out(없으면 src)에 쓴다. 실패하면 LayoutError, 파일은 그대로."""
    out = out or src
    work = tempfile.mkdtemp(prefix="hwpx-layout-")
    try:
        copy_src = os.path.join(work, "src.hwpx")  # 원본은 한글에 넘기지 않는다
        shutil.copyfile(src, copy_src)
        laid = os.path.join(work, "laid.hwpx")
        hancom_resave(copy_src, laid)
        graft(copy_src, laid, os.path.join(work, "out.hwpx"))
        shutil.copyfile(os.path.join(work, "out.hwpx"), out)
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        print(__doc__.splitlines()[0])
        sys.exit(2)
    try:
        apply_hancom_layout(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None)
    except LayoutError as e:
        print(f"한글 줄 배치 실패: {e}", file=sys.stderr)
        sys.exit(1)
