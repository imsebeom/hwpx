"""HWP(바이너리) → HWPX 변환 — rhwp 엔진 1차, 한컴오피스 COM SaveAs 폴백 (최우선 경로).

rhwp(에디터의 WASM 엔진)가 한글 없이 변환한다. 공문 HWP 4건에서 한글 COM 변환본과 한글 PDF 가
픽셀까지 같았다(2026-10-02). rhwp 가 실패한 파일만 한글 COM 으로 넘기고, 그때는 한글이
사용자 창의 포커스를 빼앗지 않게 숨은 데스크톱에서 돌린다(hidden_desktop.py).
jkf87 순수 Python 변환기(convert_hwp.py)는 표·이미지 손실이 크므로 쓰지 않는다.

    python hwp_to_hwpx_hancom.py <파일 또는 폴더> [파일2 ...]

- 파일을 주면 그 파일만, 폴더를 주면 폴더 내 *.hwp 전부 변환.
- 원본 .hwp 옆에 동일명 .hwpx 생성 (원본은 보존).
- 보안 팝업은 FilePathCheckerModule 등록으로 자동 우회.
"""

import os
import sys
import glob

sys.stdout.reconfigure(encoding="utf-8")


def _collect(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            files.extend(glob.glob(os.path.join(p, "*.hwp")))
        elif p.lower().endswith(".hwp"):
            files.append(p)
    return files


def _sig(path):
    """파일 시그니처로 실제 포맷 판별. 확장자를 신뢰하지 않는다."""
    with open(path, "rb") as fh:
        head = fh.read(4)
    if head == b"PK\x03\x04":
        return "zip"   # 실은 HWPX(ZIP). 확장자만 .hwp 인 경우
    if head == b"\xd0\xcf\x11\xe0":
        return "ole"   # 진짜 바이너리 HWP
    return "unknown"


def convert(paths):
    import shutil

    files = _collect(paths)
    if not files:
        print("변환할 .hwp 파일이 없습니다.")
        return 1

    # 실제 포맷 분류 — .hwp 확장자여도 내용이 ZIP(hwpx)이면 복사만 하면 된다.
    ole_files, zip_files, bad = [], [], []
    for f in files:
        k = _sig(f)
        (ole_files if k == "ole" else zip_files if k == "zip" else bad).append(f)

    ok = 0
    # (1) ZIP(=이미 hwpx 내용) → 복사만. COM 변환 시 표가 통째로 날아가는 함정.
    for f in zip_files:
        out = os.path.splitext(os.path.abspath(f))[0] + ".hwpx"
        shutil.copyfile(f, out)
        print("COPY(내용이 이미 hwpx):", os.path.basename(out))
        ok += 1

    # (2) 진짜 바이너리 HWP → rhwp. 한글을 띄우지 않으니 포커스도 뺏지 않는다.
    #     실패한 파일만 한컴 COM 으로 넘긴다(숨은 데스크톱에서).
    from rhwp_convert import hwp_to_hwpx

    com_files = []
    for f in ole_files:
        out = os.path.splitext(os.path.abspath(f))[0] + ".hwpx"
        if hwp_to_hwpx(f, out):
            print("OK(rhwp):", os.path.basename(out))
            ok += 1
        else:
            com_files.append(f)
    if com_files:
        import hidden_desktop

        if hidden_desktop.available():
            try:
                hidden_desktop.delegate(
                    __file__, "--com", *map(os.path.abspath, com_files), timeout=300
                )
            except RuntimeError as e:
                print("FAIL(한컴 COM):", e)
        else:
            _com_convert(com_files)
        ok += sum(
            os.path.isfile(os.path.splitext(os.path.abspath(f))[0] + ".hwpx")
            for f in com_files
        )

    for f in bad:
        print("SKIP(알 수 없는 포맷):", os.path.basename(f))

    print(f"\n완료: {ok}/{len(files)}")
    return 0 if ok == len(files) else 2


def _com_convert(ole_files):
    """한컴 COM SaveAs. 숨은 데스크톱의 자식 프로세스(--com)에서 부른다."""
    if ole_files:
        import win32com.client as win32

        hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")
        try:
            try:
                hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
            except Exception as e:
                print("보안 모듈 등록 생략(팝업이 뜰 수 있음):", e)
            for f in ole_files:
                out = os.path.splitext(os.path.abspath(f))[0] + ".hwpx"
                try:
                    # 이전 실행 산출물이 남아 있으면 "조용한 SaveAs 실패"를 성공으로
                    # 오판하므로 먼저 지운다 (원본 .hwp는 보존되니 재생성 가능).
                    if os.path.exists(out):
                        os.remove(out)
                    if not hwp.Open(os.path.abspath(f), "HWP", "forceopen:true"):
                        raise RuntimeError("한컴 Open 실패(False 반환)")
                    hwp.SaveAs(out, "HWPX", "")
                    if not os.path.isfile(out) or os.path.getsize(out) == 0:
                        raise RuntimeError("SaveAs 후 출력 파일이 없거나 0바이트")
                    print("OK(한컴 COM):", os.path.basename(out))
                except Exception as e:
                    print("FAIL:", os.path.basename(f), e)
                hwp.Clear(1)
        finally:
            # COM 서버가 도중에 죽어도 Hwp.exe가 백그라운드에 남지 않게 한다.
            try:
                hwp.Quit()
            except Exception:
                pass


if __name__ == "__main__":
    if sys.argv[1:2] == ["--com"]:
        _com_convert(sys.argv[2:])
        sys.exit(0)
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    sys.exit(convert(sys.argv[1:]))
