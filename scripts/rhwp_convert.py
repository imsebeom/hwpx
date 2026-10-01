"""rhwp 로 HWP → HWPX 변환(한글 COM 불필요). 실패하면 False 를 돌려 호출한 쪽이 한글 COM 으로 넘어가게 한다.

    from rhwp_convert import hwp_to_hwpx
    if not hwp_to_hwpx(src, dst): ...  # 한글 COM 폴백

엔진은 ① 에디터 빌드(editor/studio-dist/node, setup.mjs 가 둔다) ② ~/.cache/rhwp-core/<버전> 순으로 찾고,
둘 다 없으면 처음 한 번 npm 의 @rhwp/core 미리 빌드본을 받아 ②에 둔다(약 4MB, node 와 npm 필요).
레포를 막 받은 PC 는 setup.mjs 를 돌리지 않았으므로 ②가 쓰인다. 두 엔진의 HWP→HWPX 결과는 바이트까지
같았다(2026-10-02 공문 3건). 버전은 setup.mjs 의 RHWP_VERSION 을 따라 에디터와 어긋나지 않게 한다.
"""

import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
MJS = os.path.join(HERE, "rhwp_hwp2hwpx.mjs")
EDITOR_ENGINE = os.path.join(HERE, "..", "editor", "studio-dist", "node")


def _version():
    with open(os.path.join(HERE, "..", "editor", "setup.mjs"), encoding="utf-8") as f:
        return re.search(r"RHWP_VERSION = '([\d.]+)'", f.read()).group(1)


def _has_engine(d):
    return all(os.path.isfile(os.path.join(d, f)) for f in ("rhwp.js", "rhwp_bg.wasm"))


def engine_dir():
    """쓸 수 있는 엔진 폴더. 없으면 @rhwp/core 를 받아 두고, 그것도 안 되면 None."""
    if _has_engine(EDITOR_ENGINE):
        return os.path.abspath(EDITOR_ENGINE)
    ver = _version()
    cache = os.path.join(os.path.expanduser("~"), ".cache", "rhwp-core", ver)
    if _has_engine(cache):
        return cache
    npm = shutil.which("npm")
    if not npm:
        print(
            "rhwp 엔진이 없고 npm 도 없어 받을 수 없다(Node.js 설치 필요)",
            file=sys.stderr,
        )
        return None
    print(f"rhwp 엔진(@rhwp/core {ver})을 처음 한 번 받는다 → {cache}", file=sys.stderr)
    work = tempfile.mkdtemp(prefix="rhwp-core-")
    try:
        r = subprocess.run(
            [npm, "pack", f"@rhwp/core@{ver}", "--silent"],
            cwd=work,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        tgz = (
            os.path.join(work, (r.stdout or "").strip().splitlines()[-1])
            if r.stdout.strip()
            else ""
        )
        if r.returncode != 0 or not os.path.isfile(tgz):
            print(
                f"@rhwp/core 받기 실패: {(r.stderr or r.stdout).strip()[-200:]}",
                file=sys.stderr,
            )
            return None
        os.makedirs(cache, exist_ok=True)
        with tarfile.open(tgz) as t:
            for name in ("rhwp.js", "rhwp_bg.wasm"):
                with (
                    t.extractfile(f"package/{name}") as src,
                    open(os.path.join(cache, name), "wb") as out,
                ):
                    shutil.copyfileobj(src, out)
        return cache
    except (OSError, subprocess.TimeoutExpired, tarfile.TarError, KeyError) as e:
        print(f"@rhwp/core 받기 실패: {e}", file=sys.stderr)
        return None
    finally:
        shutil.rmtree(work, ignore_errors=True)


def hwp_to_hwpx(src, dst, timeout=120):
    if os.path.exists(dst):
        os.remove(dst)  # 남은 옛 산출물을 성공으로 오판하지 않는다
    engine = engine_dir()
    if not engine:
        print("rhwp 변환 불가, 한글 COM 으로 넘어간다", file=sys.stderr)
        return False
    try:
        r = subprocess.run(
            ["node", MJS, os.path.abspath(src), os.path.abspath(dst), engine],
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
        # node 오류는 마지막 줄이 「Node.js v24…」 버전 표기라 원인이 담긴 첫 Error 줄을 보인다
        lines = (r.stderr or r.stdout).strip().splitlines()
        err = next(
            (x for x in lines if "Error" in x), lines[-1] if lines else r.returncode
        )
        print(f"rhwp 변환 실패({err}), 한글 COM 으로 넘어간다", file=sys.stderr)
        if os.path.exists(dst):
            os.remove(dst)
    return ok
