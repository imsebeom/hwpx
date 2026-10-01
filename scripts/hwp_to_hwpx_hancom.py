"""HWP(바이너리) → HWPX 변환 — rhwp CLI(export-hwpx --verify). 한글(한컴오피스)이 필요 없다.

파일 이름은 옛 한컴 COM 경로 시절 그대로다(다른 스킬과 문서가 이 이름으로 부른다).
rhwp 변환본을 한글로 뽑은 PDF 는 한글 COM 변환본과 픽셀까지 같았다(2026-10-02 공문 4건).
엔진은 처음 쓸 때 받는다(rhwp_convert.py). Windows, macOS, Linux 에서 돈다.
jkf87 순수 Python 변환기(convert_hwp.py)는 표·이미지 손실이 크므로 쓰지 않는다.

    python hwp_to_hwpx_hancom.py <파일 또는 폴더> [파일2 ...]

- 파일을 주면 그 파일만, 폴더를 주면 폴더 내 *.hwp 전부 변환.
- 원본 .hwp 옆에 동일명 .hwpx 생성 (원본은 보존).
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
    # (1) ZIP(=이미 hwpx 내용) → 복사만. 바이너리로 못박아 열면 표가 통째로 날아가는 함정.
    for f in zip_files:
        out = os.path.splitext(os.path.abspath(f))[0] + ".hwpx"
        shutil.copyfile(f, out)
        print("COPY(내용이 이미 hwpx):", os.path.basename(out))
        ok += 1

    # (2) 진짜 바이너리 HWP → rhwp
    from rhwp_convert import hwp_to_hwpx

    for f in ole_files:
        out = os.path.splitext(os.path.abspath(f))[0] + ".hwpx"
        if hwp_to_hwpx(f, out):
            print("OK:", os.path.basename(out))
            ok += 1
        else:
            print("FAIL:", os.path.basename(f))

    for f in bad:
        print("SKIP(알 수 없는 포맷):", os.path.basename(f))

    print(f"\n완료: {ok}/{len(files)}")
    return 0 if ok == len(files) else 2


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    sys.exit(convert(sys.argv[1:]))
