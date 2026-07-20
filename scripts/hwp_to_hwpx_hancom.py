"""HWP(바이너리) → HWPX 변환 — 한컴오피스 COM SaveAs 방식 (Windows 전용, 최우선 경로).

한컴오피스가 설치된 Windows에서 표·이미지·서식을 100% 보존하며 변환한다.
jkf87 순수 Python 변환기(convert_hwp.py)는 표·이미지 손실이 크므로,
한컴이 있으면 반드시 이 경로를 먼저 쓴다.

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

    # (2) 진짜 바이너리 HWP → 한컴 COM SaveAs
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
                    print("OK:", os.path.basename(out))
                    ok += 1
                except Exception as e:
                    print("FAIL:", os.path.basename(f), e)
                hwp.Clear(1)
        finally:
            # COM 서버가 도중에 죽어도 Hwp.exe가 백그라운드에 남지 않게 한다.
            try:
                hwp.Quit()
            except Exception:
                pass

    for f in bad:
        print("SKIP(알 수 없는 포맷):", os.path.basename(f))

    print(f"\n완료: {ok}/{len(files)}")
    return 0 if ok == len(files) else 2


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    sys.exit(convert(sys.argv[1:]))
