"""한글 COM 을 보이지 않는 데스크톱에서 돌려 사용자 창의 포커스를 빼앗지 않게 한다.

    python hidden_desktop.py <명령 ...>      # 명령 하나를 숨은 데스크톱에서 실행

왜: 한글(Hwp.exe)은 COM 으로 띄워도 숨은 창 「빈 문서 1 - 한글」이 뜰 때와 프로세스가 끝날 때 전경을 가져간다.
끝날 때는 Windows 가 Z 순서의 다음 창에 포커스를 넘겨, 사용자가 쓰던 창이 아니라 그 전 창이 앞으로 나온다
(Alt+Shift+Tab 처럼 보인다). Visible=False 는 이미 숨은 창이라 소용없다. 데스크톱이 다르면 전경을 가져갈 수 없고,
COM 이 띄우는 Hwp.exe 는 호출한 프로세스의 데스크톱에 생긴다(2026-10-02 실측: 열두 번 띄우는 동안 포커스 이동 0회).

함정: 숨은 데스크톱의 대화상자는 아무도 못 본다. 제한 시간을 넘기면 그 데스크톱의 프로세스를 끝내고 실패로 돌려준다.
실행마다 데스크톱 이름을 따로 써서 다른 세션의 한글을 건드리지 않는다.
"""

import ctypes
import ctypes.wintypes as wt
import itertools
import os
import subprocess
import sys
import tempfile

PREFIX = "claude-hwp-"
_seq = itertools.count()


def active():
    """지금 숨은 데스크톱에서 도는가(자식 프로세스에서 참)."""
    if sys.platform != "win32":
        return False
    u32 = ctypes.windll.user32
    buf = ctypes.create_unicode_buffer(256)
    h = u32.GetThreadDesktop(ctypes.windll.kernel32.GetCurrentThreadId())
    u32.GetUserObjectInformationW(h, 2, buf, ctypes.sizeof(buf), None)  # UOI_NAME
    return buf.value.startswith(PREFIX)


def available():
    """숨은 데스크톱을 쓸 수 있는가. 이미 그 안이면 거짓(그 자리에서 바로 COM 을 부르면 된다)."""
    if sys.platform != "win32" or active():
        return False
    try:
        import win32service  # noqa: F401
    except ImportError:
        return False
    return True


def _kill_desktop_processes(name):
    """데스크톱에 창을 둔 프로세스(한글, 대화상자)를 끝낸다."""
    u32, k32 = ctypes.windll.user32, ctypes.windll.kernel32
    hdesk = u32.OpenDesktopW(name, 0, False, 0x0040)  # DESKTOP_ENUMERATE
    if not hdesk:
        return
    pids = set()
    proc = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

    def cb(hwnd, _):
        pid = wt.DWORD()
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        pids.add(pid.value)
        return True

    u32.EnumDesktopWindows(hdesk, proc(cb), 0)
    u32.CloseDesktop(hdesk)
    for pid in pids - {0, os.getpid()}:
        hp = k32.OpenProcess(0x0001, False, pid)  # PROCESS_TERMINATE
        if hp:
            k32.TerminateProcess(hp, 1)
            k32.CloseHandle(hp)


def run(argv, timeout=180):
    """argv 를 숨은 데스크톱에서 실행하고 (종료 코드, 출력)을 돌려준다. 시간 초과는 코드 -1."""
    import win32con
    import win32event
    import win32file
    import win32process
    import win32security
    import win32service

    name = f"{PREFIX}{os.getpid()}-{next(_seq)}"
    desk = win32service.CreateDesktop(name, 0, win32con.GENERIC_ALL, None)
    sa = win32security.SECURITY_ATTRIBUTES()
    sa.bInheritHandle = True
    fd, log = tempfile.mkstemp(prefix="hidden-desktop-", suffix=".log")
    os.close(fd)
    out = win32file.CreateFile(
        log,
        win32con.GENERIC_WRITE,
        win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
        sa,
        win32con.CREATE_ALWAYS,
        0,
        None,
    )
    nul = win32file.CreateFile(
        "NUL",
        win32con.GENERIC_READ,
        win32con.FILE_SHARE_READ,
        sa,
        win32con.OPEN_EXISTING,
        0,
        None,
    )
    si = win32process.STARTUPINFO()
    si.lpDesktop = "winsta0\\" + name
    si.dwFlags = win32con.STARTF_USESTDHANDLES
    si.hStdInput, si.hStdOutput, si.hStdError = nul, out, out
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        hp, ht, _, _ = win32process.CreateProcess(
            None,
            subprocess.list2cmdline(argv),
            None,
            None,
            True,
            win32process.CREATE_NO_WINDOW,
            env,
            None,
            si,
        )
        ht.Close()
        if (
            win32event.WaitForSingleObject(hp, int(timeout * 1000))
            == win32event.WAIT_TIMEOUT
        ):
            win32process.TerminateProcess(hp, 1)
            _kill_desktop_processes(name)
            code = -1
        else:
            code = win32process.GetExitCodeProcess(hp)
            _kill_desktop_processes(
                name
            )  # 정상 종료여도 Quit 이 남긴 한글이 있으면 데스크톱이 닫히지 않는다
        hp.Close()
    finally:
        out.Close()
        nul.Close()
        desk.CloseDesktop()
    with open(log, encoding="utf-8", errors="replace") as f:
        text = f.read()
    os.remove(log)
    if code == -1:
        text += f"\n[hidden_desktop] {timeout}초 안에 끝나지 않았다. 보이지 않는 대화상자에 막혔을 수 있다."
    return code, text


def delegate(script, flag, *args, timeout=180):
    """python <script> <flag> <args> 를 숨은 데스크톱에서 실행한다. 실패하면 출력과 함께 RuntimeError."""
    code, text = run(
        [sys.executable, os.path.abspath(script), flag, *map(str, args)], timeout
    )
    if text.strip():
        print(text.rstrip())
    if code != 0:
        raise RuntimeError(
            f"숨은 데스크톱 실행 실패(코드 {code}): {text.strip()[-300:]}"
        )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__.splitlines()[0])
        sys.exit(2)
    sys.stdout.reconfigure(encoding="utf-8")
    code, text = run(sys.argv[1:])
    print(text, end="")
    sys.exit(code)
