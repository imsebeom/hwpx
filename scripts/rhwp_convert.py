"""rhwp 엔진 창구 — 한글(한컴오피스) 없이 HWP→HWPX 변환, PDF 렌더, 빌드 마지막 줄 배치 보정을 한다.

    from rhwp_convert import hwp_to_hwpx, to_pdf, apply_layout, RhwpError

엔진 두 가지를 처음 쓸 때 받아 ~/.cache 에 둔다(레포에는 넣지 않는다). 버전은 editor/setup.mjs 의
RHWP_VERSION 을 따라 에디터와 어긋나지 않게 한다.
- rhwp CLI(GitHub 릴리스 미리 빌드본, SHA256SUMS 로 검증): HWP→HWPX(export-hwpx), PDF(export-pdf).
  Windows, macOS, Linux 판이 있다. RHWP_CLI 환경 변수로 다른 실행 파일을 지정할 수 있다.
- WASM(에디터 빌드 editor/studio-dist/node, 없으면 npm @rhwp/core): 표 높이 보정(editor/rhwp_layout.mjs).
  Node.js 가 필요하다.

검증(2026-10-02, 한글이 설치된 PC 에서 대조)
- CLI export-hwpx 결과는 WASM 변환과 바이트 동일, 그 HWPX 를 한글로 뽑은 PDF 는 한글 COM 변환본과 픽셀 동일(공문 3건).
- 더미 줄 배치 문서에 apply_layout 을 하면 rhwp PDF 쪽수가 한글과 같아지고(더미 그대로면 2쪽이 1쪽),
  그 결과를 한글로 열면 원본과 픽셀 동일(0.000~0.004%)이다. 한글이 줄 배치를 다시 계산하기 때문이다.
- CLI PDF 는 한 쪽 1~2초. 한글 PDF 와 표, 그림, 쪽 구성이 같고 일부 글리프와 대체 글꼴만 다르다.
"""

import hashlib
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
EDITOR = os.path.join(HERE, "..", "editor")
EDITOR_ENGINE = os.path.join(EDITOR, "studio-dist", "node")
FONTS = os.path.join(HERE, "..", "fonts")  # 동봉 Pretendard(OFL). 시스템에 없어도 PDF 가 이 글꼴로 나온다
CACHE = os.path.join(os.path.expanduser("~"), ".cache")
RELEASE = "https://github.com/edwardkim/rhwp/releases/download/v{ver}/{name}"
DUMMY_RE = re.compile(
    rb'horzsize="22960" flags="393216"'
)  # hwpx_helpers.LINESEG_DUMMY 의 끝 부분


class RhwpError(RuntimeError):
    pass


def _version():
    with open(os.path.join(EDITOR, "setup.mjs"), encoding="utf-8") as f:
        return re.search(r"RHWP_VERSION = '([\d.]+)'", f.read()).group(1)


def _run(args, timeout):
    r = subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if r.returncode != 0:
        lines = (r.stderr or r.stdout).strip().splitlines()
        # node 오류는 마지막 줄이 「Node.js v24…」 버전 표기라 원인이 담긴 Error 줄을 보인다
        why = next(
            (x for x in lines if "Error" in x or "오류" in x),
            lines[-1] if lines else "",
        )
        raise RhwpError(f"{os.path.basename(args[0])} 실패(코드 {r.returncode}): {why}")
    return r


# ---------------------------------------------------------------------------
# rhwp CLI
# ---------------------------------------------------------------------------


def _asset():
    machine = platform.machine().lower()
    arch = "aarch64" if machine in ("arm64", "aarch64") else "x86_64"
    if sys.platform == "win32":
        return "rhwp-v{ver}-windows-x86_64.zip"
    if sys.platform == "darwin":
        return f"rhwp-v{{ver}}-macos-{arch}.tar.gz"
    return f"rhwp-v{{ver}}-linux-{arch}.tar.gz"


def cli_path():
    """rhwp CLI 실행 파일. 없으면 GitHub 릴리스에서 받아 SHA256 을 확인하고 캐시에 둔다."""
    if os.environ.get("RHWP_CLI"):
        return os.environ["RHWP_CLI"]
    ver = _version()
    exe = "rhwp.exe" if sys.platform == "win32" else "rhwp"
    dest = os.path.join(CACHE, "rhwp", ver, exe)
    if os.path.isfile(dest):
        return dest
    name = _asset().format(ver=ver)
    print(
        f"rhwp CLI {ver} 를 처음 한 번 받는다({name}) → {os.path.dirname(dest)}",
        file=sys.stderr,
    )
    work = tempfile.mkdtemp(prefix="rhwp-cli-")
    try:
        pkg = os.path.join(work, name)
        urllib.request.urlretrieve(RELEASE.format(ver=ver, name=name), pkg)
        with urllib.request.urlopen(
            RELEASE.format(ver=ver, name="SHA256SUMS.txt")
        ) as r:
            sums = r.read().decode("utf-8")
        want = next(
            (ln.split()[0] for ln in sums.splitlines() if ln.strip().endswith(name)),
            None,
        )
        with open(pkg, "rb") as f:
            got = hashlib.sha256(f.read()).hexdigest()
        if want != got:
            raise RhwpError(f"rhwp CLI 체크섬 불일치(기대 {want}, 실제 {got})")
        if name.endswith(".zip"):
            with zipfile.ZipFile(pkg) as z:
                member = next(n for n in z.namelist() if os.path.basename(n) == exe)
                data = z.read(member)
        else:
            with tarfile.open(pkg) as t:
                member = next(
                    m for m in t.getmembers() if os.path.basename(m.name) == exe
                )
                data = t.extractfile(member).read()
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        tmp = dest + ".part"
        with open(tmp, "wb") as f:
            f.write(data)
        os.chmod(tmp, 0o755)
        os.replace(
            tmp, dest
        )  # 동시에 받은 다른 프로세스와 겹쳐도 반쯤 쓴 파일을 쓰지 않는다
        return dest
    except (OSError, StopIteration, tarfile.TarError, zipfile.BadZipFile) as e:
        raise RhwpError(f"rhwp CLI 받기 실패: {e}") from e
    finally:
        shutil.rmtree(work, ignore_errors=True)


def hwp_to_hwpx(src, dst, timeout=120):
    """HWP → HWPX. 성공하면 True, 실패하면 이유를 알리고 False."""
    if os.path.exists(dst):
        os.remove(dst)  # 남은 옛 산출물을 성공으로 오판하지 않는다
    try:
        # --verify: 산출물을 다시 읽어 IR 차이가 있으면 실패(exit 3)
        _run(
            [
                cli_path(),
                "export-hwpx",
                os.path.abspath(src),
                os.path.abspath(dst),
                "--verify",
            ],
            timeout,
        )
        with zipfile.ZipFile(dst) as z:
            if "Contents/section0.xml" not in z.namelist():
                raise RhwpError("산출물에 본문(section0.xml)이 없다")
        return True
    except (RhwpError, OSError, subprocess.TimeoutExpired, zipfile.BadZipFile) as e:
        print(f"rhwp 변환 실패: {os.path.basename(src)}: {e}", file=sys.stderr)
        if os.path.exists(dst):
            os.remove(dst)
        return False


def to_pdf(src, pdf, timeout=300):
    """HWPX/HWP → PDF. 더미 줄 배치가 든 스킬 산출물은 사본에 apply_layout 을 한 뒤 그린다."""
    src, pdf = os.path.abspath(src), os.path.abspath(pdf)
    if os.path.exists(pdf):
        os.remove(pdf)
    work = tempfile.mkdtemp(prefix="rhwp-pdf-")
    try:
        target = src
        if src.lower().endswith(".hwpx") and _has_dummy(src):
            target = os.path.join(work, "laid.hwpx")
            try:
                apply_layout(src, target)
            except (
                RhwpError
            ) as e:  # 보정을 못 해도 그림은 낸다(쪽 나눔이 어긋날 수 있다)
                print(f"WARNING: 줄 배치 보정 없이 그린다({e})", file=sys.stderr)
                target = src
        _run([cli_path(), "export-pdf", target, "-o", pdf, "--font-path", os.path.abspath(FONTS)], timeout)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    if not os.path.isfile(pdf) or os.path.getsize(pdf) == 0:
        raise RhwpError("PDF 가 생성되지 않았다")
    return pdf


# ---------------------------------------------------------------------------
# WASM (Node) — 표 높이 보정
# ---------------------------------------------------------------------------


def _has_engine(d):
    return all(os.path.isfile(os.path.join(d, f)) for f in ("rhwp.js", "rhwp_bg.wasm"))


def wasm_dir():
    """WASM 엔진 폴더(에디터 빌드 우선). 없으면 npm @rhwp/core 를 받아 둔다."""
    if _has_engine(EDITOR_ENGINE):
        return os.path.abspath(EDITOR_ENGINE)
    ver = _version()
    cache = os.path.join(CACHE, "rhwp-core", ver)
    if _has_engine(cache):
        return cache
    npm = shutil.which("npm")
    if not npm:
        raise RhwpError("Node.js(npm)가 없어 rhwp WASM 엔진을 받을 수 없다")
    print(f"rhwp WASM(@rhwp/core {ver})을 처음 한 번 받는다 → {cache}", file=sys.stderr)
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
        out = (r.stdout or "").strip().splitlines()
        tgz = os.path.join(work, out[-1]) if out else ""
        if r.returncode != 0 or not os.path.isfile(tgz):
            raise RhwpError(
                f"@rhwp/core 받기 실패: {(r.stderr or r.stdout).strip()[-200:]}"
            )
        os.makedirs(cache, exist_ok=True)
        with tarfile.open(tgz) as t:
            for name in ("rhwp.js", "rhwp_bg.wasm"):
                with (
                    t.extractfile(f"package/{name}") as s,
                    open(os.path.join(cache, name), "wb") as o,
                ):
                    shutil.copyfileobj(s, o)
        return cache
    except (OSError, subprocess.TimeoutExpired, tarfile.TarError, KeyError) as e:
        raise RhwpError(f"@rhwp/core 받기 실패: {e}") from e
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _has_dummy(path):
    with zipfile.ZipFile(path) as z:
        return any(
            DUMMY_RE.search(z.read(n))
            for n in z.namelist()
            if n.startswith("Contents/section")
        )


def apply_layout(src, out=None, timeout=120):
    """스킬이 넣은 더미 줄 배치를 걷고 rhwp 로 잰 표 높이를 적는다(editor/rhwp_layout.mjs).

    더미를 믿는 다른 구현체(rhwp 등)가 문단을 한 줄로 누르고 표를 겹치게 그리는 것을 막는다.
    한글은 열 때 줄 배치를 다시 계산하므로 한글에서의 모양은 바뀌지 않는다. 실패하면 RhwpError, 파일은 그대로.
    """
    out = out or src
    if not shutil.which("node"):
        raise RhwpError("Node.js 가 없다")
    env = dict(os.environ, RHWP_ENGINE=wasm_dir())
    fd, tmp = tempfile.mkstemp(suffix=".hwpx")
    os.close(fd)
    try:
        r = subprocess.run(
            [
                "node",
                os.path.join(EDITOR, "rhwp_layout.mjs"),
                os.path.abspath(src),
                tmp,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
        )
        if r.returncode != 0 or os.path.getsize(tmp) == 0:
            lines = (r.stderr or r.stdout).strip().splitlines()
            raise RhwpError(
                next(
                    (x for x in lines if "Error" in x),
                    lines[-1] if lines else "rhwp_layout 실패",
                )
            )
        shutil.copyfile(tmp, out)
    except subprocess.TimeoutExpired as e:
        raise RhwpError(f"rhwp_layout 시간 초과({timeout}초)") from e
    finally:
        os.remove(tmp)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    cmds = {"pdf": to_pdf, "layout": apply_layout, "hwpx": hwp_to_hwpx}
    if len(sys.argv) not in (3, 4) or sys.argv[1] not in cmds:
        print("사용: python rhwp_convert.py pdf|layout|hwpx <입력> [<출력>]")
        sys.exit(2)
    try:
        res = cmds[sys.argv[1]](*sys.argv[2:])
    except RhwpError as e:
        print(f"실패: {e}", file=sys.stderr)
        sys.exit(1)
    sys.exit(1 if res is False else 0)
