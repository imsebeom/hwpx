"""hwpx 파일을 HWPX 에디터로 띄워 Aside 브라우저 탭에 연다(창 없이 pythonw 로 실행).

    pythonw aside_open.pyw <문서.hwpx>    연다 (탐색기, Aside 다운로드 「열기」가 부른다)
    python  aside_open.pyw --install      .hwpx 연결 후보 「HWPX 에디터 (Aside)」 등록(HKCU)
    python  aside_open.pyw --uninstall    등록 해제

Windows 11 은 기본 연결 프로그램을 해시(UserChoice)로 지켜 프로그램이 바꿀 수 없다.
--install 은 후보만 등록하고, 기본값은 사용자가 「연결 프로그램 > 항상」으로 한 번 고른다.
인스턴스는 파일 경로의 해시로 나눈다. 같은 파일은 떠 있는 에디터를 다시 쓰고, 다른 파일은 따로 띄운다.
"""

import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request
import winreg
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASIDE = r"C:\Program Files\Aside\Application\Aside.exe"
PROGID = "HwpxEditor.Aside"
ROOT = Path.home() / ".claude" / "cache" / "hwpx-editor"
LOG = ROOT / "aside-open.log"
NO_WINDOW = 0x08000000


def log(msg):
    ROOT.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")


def health(port):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1.5) as r:
            return json.loads(r.read())
    except Exception:
        return None


def open_file(file):
    file = str(Path(file).resolve())
    instance = "aside-" + hashlib.sha1(file.lower().encode("utf-8")).hexdigest()[:8]
    state = ROOT / instance
    env = {**os.environ, "HWPX_EDITOR_INSTANCE": instance}
    env.pop("CLAUDE_CODE_SESSION_ID", None)
    port_file = state / "port"
    old_port = port_file.read_text().strip() if port_file.exists() else ""
    had_tab = bool(old_port) and bool((health(old_port) or {}).get("browser"))

    # --no-browser: 탭은 아래에서 Aside 로 직접 연다. 탭이 이미 붙어 있으면 start 가 그 탭에 다시 연다
    proc = subprocess.Popen(
        ["node", str(HERE / "cli.mjs"), "start", file, "--browser", "--no-browser"],
        env=env,
        cwd=str(Path(file).parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        creationflags=NO_WINDOW,
    )
    if had_tab:
        out = proc.communicate(timeout=120)[0].decode("utf-8", "replace")
        log(f"재사용 {instance} {file} rc={proc.returncode} {out.strip()}")
        return

    # 새 서버가 port 파일을 쓰고 health 에 답할 때까지 기다렸다가 탭을 연다(start 는 탭이 문서를 읽을 때까지 기다린다)
    for _ in range(100):
        if proc.poll() is not None:
            break
        port = port_file.read_text().strip() if port_file.exists() else ""
        h = health(port) if port else None
        if h and Path(h.get("stateDir", "")).resolve() == state.resolve():
            subprocess.Popen([ASIDE, f"http://localhost:{port}/"], creationflags=NO_WINDOW)
            break
        time.sleep(0.2)
    out = proc.communicate(timeout=120)[0].decode("utf-8", "replace")
    log(f"열기 {instance} {file} rc={proc.returncode} {out.strip()}")
    if proc.returncode:
        subprocess.Popen(["msg", "*", f"HWPX 에디터로 열지 못했다:\n{out.strip()[-400:]}"], creationflags=NO_WINDOW)


def install():
    pyw = str(Path(sys.executable).with_name("pythonw.exe"))
    cmd = f'"{pyw}" "{Path(__file__).resolve()}" "%1"'
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{PROGID}") as k:
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "HWPX 문서 (HWPX 에디터)")
        winreg.SetValueEx(k, "FriendlyTypeName", 0, winreg.REG_SZ, "HWPX 에디터 (Aside)")
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{PROGID}\shell\open") as k:
        winreg.SetValueEx(k, "FriendlyAppName", 0, winreg.REG_SZ, "HWPX 에디터 (Aside)")
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{PROGID}\shell\open\command") as k:
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, cmd)
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.hwpx\OpenWithProgids") as k:
        winreg.SetValueEx(k, PROGID, 0, winreg.REG_NONE, b"")
    print(f"등록: {PROGID}\n  {cmd}")


def uninstall():
    for sub in [r"shell\open\command", r"shell\open", "shell", ""]:
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{PROGID}\{sub}".rstrip("\\"))
        except FileNotFoundError:
            pass
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.hwpx\OpenWithProgids", 0, winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, PROGID)
    except FileNotFoundError:
        pass
    print(f"해제: {PROGID}")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "--install":
        install()
    elif arg == "--uninstall":
        uninstall()
    elif arg:
        try:
            open_file(arg)
        except Exception as e:
            log(f"오류 {arg} {e!r}")
            raise
    else:
        print(__doc__)
