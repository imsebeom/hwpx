"""hancom_layout.py <원본.hwpx> [<출력.hwpx>]  — 출력을 빼면 원본을 고친다.

한글(COM)로 사본을 열어 저장하고, 그 저장본의 줄 배치(linesegarray)와 표 높이(hp:tbl/hp:sz height)만
원본에 옮겨 심는다. 나머지(그림, 서식, 칸 높이)는 원본 그대로다.

왜: 스킬이 XML 을 직접 조립하면 줄 배치를 계산할 수 없어 한 줄짜리 더미(hwpx_helpers.LINESEG_DUMMY)를 넣고
칸 높이를 한 줄 기준으로 적는다. 한글은 열 때 다시 조판하지만 rhwp 같은 다른 구현체는 더미를 믿어 문단을
한 줄로 누르고, 더미를 걷어도 글자처럼 취급하는 표의 행을 늘리지 못해 아래 표와 겹친다(rhwp 결함).
한글이 계산한 줄 배치와 표 높이를 넣으면 rhwp 가 한글 재저장본과 글자 좌표까지 같게 그린다(2026-09-25 실측).
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


def _pid_alive(pid):
    """Windows 에서 os.kill(pid, 0) 은 프로세스를 끝내 버리므로 OpenProcess 로 살핀다."""
    if os.name != "nt":
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    import ctypes

    k = ctypes.windll.kernel32
    h = k.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False
    code = ctypes.c_ulong()
    ok = k.GetExitCodeProcess(h, ctypes.byref(code))
    k.CloseHandle(h)
    return bool(ok) and code.value == 259  # STILL_ACTIVE


def _lock_owner_dead():
    try:
        pid = int(open(LOCK, encoding="ascii").read().strip() or 0)
    except (OSError, ValueError):
        return False
    return pid > 0 and not _pid_alive(pid)


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
                # 죽은 프로세스가 남긴 잠금. 주인 PID 가 없으면 바로, 읽지 못하면 5분 뒤 지운다
                # (2026-10-01 중단된 빌드가 남긴 잠금에 다음 빌드가 3분 넘게 멈췄다)
                if _lock_owner_dead() or time.time() - os.path.getmtime(LOCK) > 300:
                    os.remove(LOCK)
                    continue
            except OSError:
                pass
            if time.time() - start > timeout:
                raise LayoutError("다른 한글 조판 작업이 끝나지 않는다(잠금 대기 초과)")
            time.sleep(0.5)


def hancom_resave(src, dst):
    import hidden_desktop

    # 한글이 사용자 창의 포커스를 빼앗지 않게 숨은 데스크톱의 자식 프로세스에서 연다(hidden_desktop.py).
    hidden = hidden_desktop.available()
    w = None
    if not hidden:
        try:
            import win32com.client as w
        except ImportError as e:
            raise LayoutError("pywin32 가 없다(한글 COM 불가)") from e
    src, dst = os.path.abspath(src), os.path.abspath(dst)
    _acquire_lock()
    try:
        # 앞 작업이 닫는 중인 한글에 붙으면 띄우기나 작업 도중에 RPC 오류가 난다(2026-09-25 동시 실행 실측).
        # 띄우기부터 저장까지를 통째로 다시 시도한다.
        last = None
        for _ in range(3):
            try:
                if hidden:
                    # 에디터 서버가 이 스크립트를 120초에 끊으므로 두 번은 시도할 수 있게 45초로 둔다.
                    # 끊기면 손자 프로세스는 남아 대화상자에 영영 막힐 수 있다.
                    hidden_desktop.delegate(
                        __file__, "--resave-once", src, dst, timeout=45
                    )
                else:
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
        # 쪽수를 물어야 끝까지 조판한다. 묻지 않고 저장하면 원래 줄 배치를 그대로 쓴다(2026-09-25 실측).
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
    if sys.argv[1:2] == ["--resave-once"]:  # hancom_resave 가 숨은 데스크톱에서 부른다
        import win32com.client

        _resave_once(win32com.client, *map(os.path.abspath, sys.argv[2:4]))
        sys.exit(0)
    if len(sys.argv) not in (2, 3):
        print(__doc__.splitlines()[0])
        sys.exit(2)
    try:
        apply_hancom_layout(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None)
    except LayoutError as e:
        print(f"한글 줄 배치 실패: {e}", file=sys.stderr)
        sys.exit(1)
