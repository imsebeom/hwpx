"""rhwp 로 HWP → HWPX 변환(한글 COM 불필요). 실패하면 False 를 돌려 호출한 쪽이 한글 COM 으로 넘어가게 한다.

from rhwp_convert import hwp_to_hwpx
if not hwp_to_hwpx(src, dst): ...  # 한글 COM 폴백
"""

import os
import subprocess
import sys
import zipfile

MJS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rhwp_hwp2hwpx.mjs")


def hwp_to_hwpx(src, dst, timeout=120):
    if os.path.exists(dst):
        os.remove(dst)  # 남은 옛 산출물을 성공으로 오판하지 않는다
    try:
        r = subprocess.run(
            ["node", MJS, os.path.abspath(src), os.path.abspath(dst)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"rhwp 변환 실패({e}), 한글 COM 으로 넘어간다", file=sys.stderr)
        return False
    try:
        with zipfile.ZipFile(dst) as z:
            ok = r.returncode == 0 and "Contents/section0.xml" in z.namelist()
    except (OSError, zipfile.BadZipFile):
        ok = False
    if not ok:
        err = (r.stderr or r.stdout).strip().splitlines()
        print(
            f"rhwp 변환 실패({err[-1] if err else r.returncode}), 한글 COM 으로 넘어간다",
            file=sys.stderr,
        )
        if os.path.exists(dst):
            os.remove(dst)
    return ok
