"""
HWPX 양식 채우기 게이트 — 플레이스홀더 템플릿 강제

원본 양식에 값을 바로 써 넣는 것을 차단하고 아래 3단계를 강제한다.

    [1] 템플릿 제작 : 채울 자리를 {{필드명}} 플레이스홀더로 만든다
    [2] 사용자 확인 : PDF/PNG 로 렌더해 보여주고 approve 로 승인 기록을 남긴다
    [3] 값 채우기   : 승인된 템플릿에만 실제 값을 넣는다

매니페스트는 템플릿 파일 옆에 `<템플릿명>.hwpx.gate.json` 으로 저장된다.
승인 이후 템플릿이 바뀌면 해시가 달라져 승인이 자동으로 무효가 된다.

CLI:
    form_gate.py scan     <hwpx>                 플레이스홀더 목록·게이트 상태
    form_gate.py make     <원본> <템플릿> [--table N]  표 내용 셀 자동 플레이스홀더화
    form_gate.py preview  <템플릿> [--pages N]   PDF/PNG 미리보기 생성
    form_gate.py approve  <템플릿> [--note ...]  사용자 확인 기록
    form_gate.py status   <hwpx>                 채우기 가능 여부 (exit 0/2)
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

MANIFEST_SUFFIX = ".gate.json"
MANIFEST_VERSION = 1

# {{필드}} 를 기본으로 하되 워크플로우 L 의 {학교명} 단일 중괄호도 인정한다.
# 단일 중괄호는 글자·숫자·밑줄·공백만 허용한다 — 공문 본문의 수식·버튼 표기
# (`{1-2×(제안가격/제안평균가격-95/100)}`, `{(100,000원×1시간)+...}`)가 플레이스홀더로
# 오탐되던 것을 막는다 (실측: 문서 1,227개 스캔에서 다수 검출)
PLACEHOLDER_RE = re.compile(r"\{\{[^{}\n]{1,60}\}\}|\{\w[\w ]{0,28}\}")
_T_RE = re.compile(r"<hp:t[^>]*>(.*?)</hp:t>", re.DOTALL)
_P_RE = re.compile(r"<hp:p[ >].*?</hp:p>", re.DOTALL)

SKIP_FLAG = "--skip-template-gate"


class TemplateGateError(RuntimeError):
    """플레이스홀더 템플릿 게이트 위반"""


# ---------------------------------------------------------------------------
# 플레이스홀더 판별
# ---------------------------------------------------------------------------

def is_placeholder(value: Any) -> bool:
    """문자열 전체가 플레이스홀더 하나인가"""
    if not isinstance(value, str):
        return False
    s = value.strip()
    m = PLACEHOLDER_RE.fullmatch(s)
    return m is not None


def is_template_write(values: Iterable[Any]) -> bool:
    """쓰려는 값이 전부 플레이스홀더면 템플릿 제작으로 본다 (빈 값은 무시)"""
    meaningful = [v for v in values if isinstance(v, str) and v.strip()]
    if not meaningful:
        return True
    return all(is_placeholder(v) for v in meaningful)


def scan_placeholders(hwpx_path: str) -> Dict[str, List[str]]:
    """HWPX 본문에서 플레이스홀더를 수집한다.

    Returns:
        {"ok": [단일 hp:t 안에 온전한 것], "split": [문단에는 있으나 run 이 쪼개진 것]}
    """
    ok: List[str] = []
    split: List[str] = []

    with zipfile.ZipFile(hwpx_path, "r") as zf:
        for name in zf.namelist():
            if not (name.startswith("Contents/") and name.endswith(".xml")):
                continue
            try:
                xml = zf.read(name).decode("utf-8")
            except UnicodeDecodeError:
                continue

            for t in _T_RE.findall(xml):
                ok.extend(PLACEHOLDER_RE.findall(t))

            # 문단 단위로 이어붙여 run 이 쪼개진 플레이스홀더를 찾는다
            for p in _P_RE.findall(xml):
                joined = "".join(_T_RE.findall(p))
                for ph in PLACEHOLDER_RE.findall(joined):
                    if ph not in ok:
                        split.append(ph)

    return {"ok": sorted(set(ok)), "split": sorted(set(split))}


# ---------------------------------------------------------------------------
# 매니페스트
# ---------------------------------------------------------------------------

def manifest_path(hwpx_path: str) -> Path:
    return Path(str(hwpx_path) + MANIFEST_SUFFIX)


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_manifest(hwpx_path: str) -> Optional[Dict[str, Any]]:
    mp = manifest_path(hwpx_path)
    if not mp.exists():
        return None
    try:
        return json.loads(mp.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def write_manifest(hwpx_path: str, data: Dict[str, Any]) -> Path:
    mp = manifest_path(hwpx_path)
    mp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return mp


def record_template(template_path: str, source: Optional[str] = None,
                    note: Optional[str] = None) -> Dict[str, Any]:
    """템플릿 제작 결과를 매니페스트에 기록한다 (미승인 상태).

    이미 승인된 매니페스트가 있고 파일이 그대로면 승인을 유지한다.
    """
    found = scan_placeholders(template_path)
    if not found["ok"]:
        raise TemplateGateError(
            f"플레이스홀더가 하나도 없다: {template_path}\n"
            f"  채울 자리를 {{{{필드명}}}} 형태로 넣은 뒤 다시 기록하라."
        )

    digest = sha256(template_path)
    prev = read_manifest(template_path) or {}
    keep_approval = bool(prev.get("approved")) and prev.get("template_sha256") == digest

    data = {
        "version": MANIFEST_VERSION,
        "template": os.path.basename(template_path),
        "template_sha256": digest,
        "source": os.path.basename(source) if source else prev.get("source"),
        "placeholders": found["ok"],
        "split_placeholders": found["split"],
        "created_at": prev.get("created_at") or datetime.now().isoformat(timespec="seconds"),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "preview": prev.get("preview", []) if keep_approval else [],
        "approved": keep_approval,
        "approved_at": prev.get("approved_at") if keep_approval else None,
        "approved_note": note or (prev.get("approved_note") if keep_approval else None),
    }
    write_manifest(template_path, data)
    return data


def approve(template_path: str, note: Optional[str] = None,
            no_preview: bool = False, pages: int = 2) -> Dict[str, Any]:
    """사용자 확인을 기록한다. 미리보기 PNG 가 없으면 먼저 생성한다."""
    data = read_manifest(template_path)
    if not data or data.get("template_sha256") != sha256(template_path):
        data = record_template(template_path)

    previews = [p for p in data.get("preview", []) if os.path.exists(p)]
    if not previews and not no_preview:
        try:
            previews = render_preview(template_path, pages=pages)
        except Exception as e:  # 한컴 미설치·COM 실패 등
            raise TemplateGateError(
                f"미리보기 생성 실패: {e}\n"
                f"  사용자가 템플릿을 직접 열어 확인했다면 --no-preview 로 승인하라."
            ) from e

    data["preview"] = previews
    data["approved"] = True
    data["approved_at"] = datetime.now().isoformat(timespec="seconds")
    data["approved_note"] = note
    write_manifest(template_path, data)
    return data


# ---------------------------------------------------------------------------
# 게이트 검사
# ---------------------------------------------------------------------------

def require_approved(hwpx_path: str, action: str = "값 채우기",
                     skip: bool = False) -> Optional[Dict[str, Any]]:
    """승인된 플레이스홀더 템플릿인지 확인한다. 아니면 TemplateGateError."""
    if skip:
        print(f"[게이트 우회] {SKIP_FLAG} 지정 — {action} 을 검사 없이 진행한다.",
              file=sys.stderr)
        return None

    name = os.path.basename(hwpx_path)
    data = read_manifest(hwpx_path)

    if data is None:
        raise TemplateGateError(
            f"승인된 플레이스홀더 템플릿이 아니다: {name}\n"
            f"  원본 양식에 값을 바로 채울 수 없다. 다음 순서를 따르라.\n"
            f"  [1] 템플릿 제작 : form_gate.py make <원본> <템플릿> "
            f"(또는 채울 자리에 {{{{필드명}}}} 삽입)\n"
            f"  [2] 사용자 확인 : form_gate.py preview <템플릿> → 사용자에게 제시\n"
            f"  [3] 승인 기록   : form_gate.py approve <템플릿>\n"
            f"  검사를 건너뛰려면 {SKIP_FLAG}"
        )

    if not data.get("approved"):
        raise TemplateGateError(
            f"템플릿이 아직 승인되지 않았다: {name}\n"
            f"  플레이스홀더 {len(data.get('placeholders', []))}개 — "
            f"{', '.join(data.get('placeholders', [])[:5])}\n"
            f"  사용자에게 미리보기를 제시한 뒤 "
            f"form_gate.py approve \"{hwpx_path}\" 를 실행하라."
        )

    if data.get("template_sha256") != sha256(hwpx_path):
        raise TemplateGateError(
            f"승인 이후 템플릿이 변경되었다: {name}\n"
            f"  변경본을 다시 제시하고 form_gate.py approve 로 재승인하라."
        )

    found = scan_placeholders(hwpx_path)
    if not found["ok"]:
        raise TemplateGateError(
            f"템플릿에 남은 플레이스홀더가 없다: {name}\n"
            f"  이미 값이 채워진 산출물로 보인다. 템플릿 원본을 대상으로 실행하라."
        )
    return data


def guard_write(target_path: str, values: Iterable[Any], action: str,
                skip: bool = False) -> bool:
    """쓰기 작업 진입점. 템플릿 제작이면 통과, 값 채우기면 승인 검사.

    Returns:
        True 면 템플릿 제작(플레이스홀더 쓰기), False 면 값 채우기
    """
    if is_template_write(values):
        return True
    require_approved(target_path, action=action, skip=skip)
    return False


# ---------------------------------------------------------------------------
# 미리보기 (한컴 COM → PDF → pdftoppm PNG)
# ---------------------------------------------------------------------------

def _pdftoppm() -> Optional[str]:
    exe = shutil.which("pdftoppm")
    if exe:
        return exe
    fallback = r"C:\poppler\Library\bin\pdftoppm.exe"
    return fallback if os.path.exists(fallback) else None


def _hancom_to_pdf(src: str, pdf_path: str) -> None:
    """한컴 COM 으로 HWPX 를 PDF 로 저장한다 (경로는 반드시 절대 경로)."""
    import win32com.client as win32  # 한컴 COM (Windows 전용)

    hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")
    try:
        hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
        # 한글 창이 떠서 사용자가 쓰던 창의 포커스를 빼앗는 것을 막는다.
        # 다른 문서가 이미 열려 있으면(Count>1) 남의 창을 숨길 수 있으므로 건드리지 않는다.
        try:
            if hwp.XHwpWindows.Count == 1:
                hwp.XHwpWindows.Active_XHwpWindow.Visible = False
        except Exception:
            pass
        if not hwp.Open(src, "", "forceopen:true"):
            raise RuntimeError(f"한글이 파일을 열지 못했다: {src}")
        hwp.SaveAs(pdf_path, "PDF", "")
        hwp.Clear(1)
    finally:
        # COM 서버가 도중에 죽어도 Hwp.exe 가 백그라운드에 남지 않게 한다
        try:
            hwp.Quit()
        except Exception:
            pass

    if not os.path.isfile(pdf_path) or os.path.getsize(pdf_path) == 0:
        raise RuntimeError("PDF 가 생성되지 않았다")


def render_preview(hwpx_path: str, out_dir: Optional[str] = None,
                   pages: int = 2, dpi: int = 110) -> List[str]:
    """템플릿을 PDF 로 변환하고 앞 몇 쪽을 PNG 로 만든다."""
    # 한컴 COM 서버는 별도 프로세스(CWD=한컴 Bin)라 상대 경로를 자기 폴더 기준으로
    # 해석한다. 반드시 절대 경로로 넘긴다.
    src = os.path.abspath(hwpx_path)
    out = Path(out_dir).resolve() if out_dir else Path(src).parent / "_preview"
    out.mkdir(parents=True, exist_ok=True)
    stem = Path(src).stem
    pdf_path = str(out / f"{stem}.pdf")

    # 상대 경로를 넘기면 한컴이 자기 Bin 폴더에 저장을 시도해 다이얼로그가 뜨고,
    # 그 다이얼로그가 후속 COM 호출을 전부 블록한다 (2026-07-20 /md 동일 사고)
    assert os.path.isabs(src) and os.path.isabs(pdf_path), "한컴 COM 에는 절대 경로만"

    # 이전 산출물이 남아 있으면 조용한 SaveAs 실패를 성공으로 오판한다
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    for old in out.glob(f"{stem}-*.png"):   # 옛 PNG가 남으면 쪽 수가 실제보다 많아 보인다
        old.unlink()

    # COM 인스턴스 재생성은 연속 호출에서 산발적으로 실패한다 (RPC 오류)
    last_err = None
    for attempt in range(2):
        try:
            _hancom_to_pdf(src, pdf_path)
            last_err = None
            break
        except Exception as e:
            last_err = e
            time.sleep(2)
    if last_err is not None:
        raise RuntimeError(f"한컴 PDF 변환 실패: {last_err}")

    exe = _pdftoppm()
    if not exe:
        return [pdf_path]

    subprocess.run(
        [exe, "-r", str(dpi), "-png", "-f", "1", "-l", str(pages),
         pdf_path, str(out / stem)],
        check=True, capture_output=True,
    )
    pngs = sorted(str(p) for p in out.glob(f"{stem}-*.png"))
    # 앞 N쪽만 PNG로 만들므로 뒤쪽 표가 통째로 안 보일 수 있다 (2026-09-13 강의일지 3쪽 중 충실도 표를 못 봄)
    total = _pdf_pages(exe, pdf_path)
    if total and total > pages:
        import sys
        print(f"⚠ PDF {total}쪽 중 앞 {pages}쪽만 PNG로 만들었다. 나머지는 --pages {total} 로 다시 뽑거나 {pdf_path} 를 직접 본다",
              file=sys.stderr)
    return pngs or [pdf_path]


def _pdf_pages(pdftoppm_exe: str, pdf_path: str) -> Optional[int]:
    """pdftoppm 옆의 pdfinfo 로 총 쪽 수. 없으면 None."""
    info = Path(pdftoppm_exe).with_name("pdfinfo" + Path(pdftoppm_exe).suffix)
    if not info.exists():
        return None
    try:
        # 한글 경로가 cp949로 섞여 나오므로 text=True(utf-8)로 받으면 디코딩에서 죽는다. Pages 줄은 ASCII다
        r = subprocess.run([str(info), pdf_path], capture_output=True, check=True)
    except Exception:
        return None
    m = re.search(r"^Pages:\s+(\d+)", r.stdout.decode("utf-8", errors="ignore"), re.M)
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------------------
# 템플릿 제작 (표 내용 셀 자동 플레이스홀더화)
# ---------------------------------------------------------------------------

def make_template(source: str, output: str, table_index: int = 0) -> Dict[str, Any]:
    """원본 양식의 표 내용 셀을 {{레이블}} 플레이스홀더로 바꾼 템플릿을 만든다."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from hwpx_form_filler import HwpxFormFiller

    with HwpxFormFiller(source) as form:
        placeholders = form.set_placeholders(table_index=table_index)
        form.save(output)

    data = record_template(output, source=source)
    data["cells"] = {ph: list(rc) for ph, rc in placeholders.items()}
    write_manifest(output, data)
    return data


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def find_templates(root: str) -> List[str]:
    """디렉터리에서 플레이스홀더를 가진 hwpx 를 찾는다 (기존 양식 일괄 승인용)."""
    hits = []
    for p in sorted(Path(root).rglob("*.hwpx")):
        if any(part in (".git", "_preview", "_check") for part in p.parts):
            continue
        try:
            if scan_placeholders(str(p))["ok"]:
                hits.append(str(p))
        except (zipfile.BadZipFile, OSError):
            continue
    return hits


def _print_scan(hwpx_path: str) -> None:
    found = scan_placeholders(hwpx_path)
    data = read_manifest(hwpx_path)
    print(f"파일: {hwpx_path}")
    print(f"플레이스홀더 {len(found['ok'])}개: {', '.join(found['ok']) or '없음'}")
    single = [p for p in found["ok"] if not p.startswith("{{")]
    if single:
        print(f"  ※ 단일 중괄호 {len(single)}개 — 본문의 버튼명·용어 표기일 수 있으니 "
              f"승인 전에 확인하라: {', '.join(single[:5])}")
    if found["split"]:
        print(f"⚠ run 이 쪼개진 플레이스홀더 {len(found['split'])}개: "
              f"{', '.join(found['split'])}")
        print("  → 그대로 두면 치환이 실패한다. 해당 셀을 다시 입력하라.")
    if data is None:
        print("게이트: 매니페스트 없음 (값 채우기 불가)")
    else:
        state = "승인됨" if data.get("approved") else "미승인"
        if data.get("approved") and data.get("template_sha256") != sha256(hwpx_path):
            state = "승인 후 변경됨 (무효)"
        print(f"게이트: {state}")
        if data.get("preview"):
            print(f"미리보기: {', '.join(data['preview'])}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="HWPX 양식 채우기 게이트 (템플릿 제작 → 사용자 확인 → 채우기)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("scan", help="플레이스홀더 목록·게이트 상태 (디렉터리면 재귀 탐색)")
    p.add_argument("hwpx")

    p = sub.add_parser("make", help="표 내용 셀을 플레이스홀더로 바꾼 템플릿 생성")
    p.add_argument("source")
    p.add_argument("output")
    p.add_argument("--table", type=int, default=0)

    p = sub.add_parser("preview", help="PDF/PNG 미리보기 생성")
    p.add_argument("hwpx")
    p.add_argument("--pages", type=int, default=2)
    p.add_argument("--out")

    p = sub.add_parser("approve", help="사용자 확인 기록 (여러 파일 지정 가능)")
    p.add_argument("hwpx", nargs="+")
    p.add_argument("--note")
    p.add_argument("--no-preview", action="store_true",
                   help="사용자가 직접 열어 확인한 경우 렌더 없이 승인")
    p.add_argument("--pages", type=int, default=2)

    p = sub.add_parser("status", help="값 채우기 가능 여부 (exit 0/2)")
    p.add_argument("hwpx")

    args = parser.parse_args(argv)

    try:
        if args.cmd == "scan":
            if os.path.isdir(args.hwpx):
                hits = find_templates(args.hwpx)
                print(f"플레이스홀더를 가진 hwpx {len(hits)}개")
                for h in hits:
                    data = read_manifest(h)
                    state = "승인됨" if data and data.get("approved") else "미승인"
                    print(f"  [{state}] {h}")
            else:
                _print_scan(args.hwpx)
        elif args.cmd == "make":
            data = make_template(args.source, args.output, args.table)
            print(f"템플릿 생성: {args.output}")
            print(f"플레이스홀더 {len(data['placeholders'])}개: "
                  f"{', '.join(data['placeholders'])}")
            print("다음: form_gate.py preview → 사용자 확인 → form_gate.py approve")
        elif args.cmd == "preview":
            paths = render_preview(args.hwpx, args.out, pages=args.pages)
            print("\n".join(paths))
        elif args.cmd == "approve":
            for path in args.hwpx:
                data = approve(path, args.note, args.no_preview, args.pages)
                print(f"승인: {path} — 플레이스홀더 {len(data['placeholders'])}개 "
                      f"({data['approved_at']})")
        elif args.cmd == "status":
            require_approved(args.hwpx)
            print("통과: 승인된 플레이스홀더 템플릿")
    except TemplateGateError as e:
        print(f"[게이트 차단] {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
