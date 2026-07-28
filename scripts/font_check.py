#!/usr/bin/env python3
"""문서가 참조하는 글꼴이 실제로 있는지 확인한다 — 표준 라이브러리만 사용.

KS X 6101:2024 9.3.2.2.2:
  - @isEmbedded가 참이면 컨테이너에 글꼴이 내장되어 있고 @binaryItemIDRef가
    유효해야 한다. 아니면 애플리케이션은 오류 상황으로 인식해야 한다.
  - @isEmbedded가 거짓인데 시스템에 그 글꼴이 없으면 역시 오류 상황이며,
    <substFont>(대체 글꼴)를 먼저 쓰고 없으면 시스템 기본 글꼴을 권고한다.

글꼴이 없으면 한컴이 임의로 대체해 자간·줄수가 달라지고 쪽 나눔이 밀린다.
문서가 열리기는 하므로 조용히 넘어가기 쉬운 결함이다.

사용:
    python font_check.py document.hwpx
"""

from __future__ import annotations

import re
import struct
import sys
import zipfile
from pathlib import Path

# 한컴오피스 기본 내장 글꼴 — 한컴이 설치된 환경이면 있다고 본다
HANCOM_BUNDLED = {
    "함초롬바탕", "함초롬돋움", "한컴바탕", "한컴돋움", "한컴솔체",
    "한컴산뜻돋움", "한컴백제M", "한컴 윤고딕 230", "한컴 윤고딕 240",
    "HY헤드라인M", "HY견고딕", "HY중고딕", "HY신명조", "HY궁서",
    "휴먼명조", "휴먼고딕", "한양신명조", "한양중고딕",
}

FONT_DIRS = [
    Path("C:/Windows/Fonts"),
    Path.home() / "AppData/Local/Microsoft/Windows/Fonts",
    Path("/usr/share/fonts"),
    Path("/usr/local/share/fonts"),
    Path.home() / ".fonts",
    Path("/Library/Fonts"),
    Path("/System/Library/Fonts"),
]


def _read_ttf_names(path: Path) -> set[str]:
    """TTF/OTF/TTC의 name 테이블에서 패밀리 이름을 뽑는다."""
    names: set[str] = set()
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return names
    if len(data) < 12:
        return names

    offsets = []
    if data[:4] == b"ttcf":
        count = struct.unpack(">I", data[8:12])[0]
        for i in range(min(count, 32)):
            pos = 12 + i * 4
            if pos + 4 <= len(data):
                offsets.append(struct.unpack(">I", data[pos : pos + 4])[0])
    else:
        offsets.append(0)

    for base in offsets:
        try:
            num_tables = struct.unpack(">H", data[base + 4 : base + 6])[0]
            for i in range(num_tables):
                rec = base + 12 + i * 16
                tag = data[rec : rec + 4]
                if tag != b"name":
                    continue
                tbl_off, tbl_len = struct.unpack(">II", data[rec + 8 : rec + 16])
                fmt, count, str_off = struct.unpack(
                    ">HHH", data[tbl_off : tbl_off + 6]
                )
                storage = tbl_off + str_off
                for j in range(count):
                    r = tbl_off + 6 + j * 12
                    pid, eid, lid, nid, ln, off = struct.unpack(
                        ">HHHHHH", data[r : r + 12]
                    )
                    if nid not in (1, 16):  # family, typographic family
                        continue
                    raw = data[storage + off : storage + off + ln]
                    try:
                        if pid == 3 or (pid == 0):
                            names.add(raw.decode("utf-16-be").strip())
                        else:
                            names.add(raw.decode("latin-1").strip())
                    except (UnicodeDecodeError, ValueError):
                        continue
        except (struct.error, IndexError):
            continue
    return {n for n in names if n}


def system_fonts(limit: int = 3000) -> set[str]:
    """설치된 글꼴 패밀리 이름 집합. 웹 컨테이너처럼 폰트가 없으면 빈 집합."""
    found: set[str] = set()
    scanned = 0
    for d in FONT_DIRS:
        if not d.is_dir():
            continue
        for p in d.rglob("*"):
            if scanned >= limit:
                break
            if p.suffix.lower() in (".ttf", ".otf", ".ttc"):
                found |= _read_ttf_names(p)
                scanned += 1
    return found


def check(path: str | Path, *, installed: set[str] | None = None) -> dict:
    """문서의 글꼴 사용 현황을 조사한다."""
    path = Path(path)
    with zipfile.ZipFile(path) as zf:
        header = zf.read("Contents/header.xml").decode("utf-8", "replace")
        bindata = {n for n in zf.namelist() if n.startswith("BinData/")}
        hpf = ""
        if "Contents/content.hpf" in zf.namelist():
            hpf = zf.read("Contents/content.hpf").decode("utf-8", "replace")
        sections = [
            zf.read(n).decode("utf-8", "replace")
            for n in zf.namelist()
            if n.startswith("Contents/section") and n.endswith(".xml")
        ]

    # 실제로 본문에서 참조되는 charPr만 추린다
    used_charpr = set()
    for s in sections:
        used_charpr |= {int(x) for x in re.findall(r'charPrIDRef="(\d+)"', s)}

    # charPr → fontRef(글꼴 id)
    charpr_fonts: dict[int, set[int]] = {}
    for m in re.finditer(r"<hh:charPr\b[^>]*\bid=\"(\d+)\".*?</hh:charPr>", header, re.S):
        cid = int(m.group(1))
        ref = re.search(r"<hh:fontRef\b([^/]*)/>", m.group(0))
        ids = set()
        if ref:
            ids = {int(v) for v in re.findall(r'"(\d+)"', ref.group(1))}
        charpr_fonts[cid] = ids

    # lang별 글꼴 목록
    fonts: dict[int, dict] = {}
    for fm in re.finditer(
        r'<hh:fontface lang="(\w+)"[^>]*>(.*?)</hh:fontface>', header, re.S
    ):
        lang, block = fm.group(1), fm.group(2)
        for f in re.finditer(r"<hh:font\b([^>]*)>", block):
            attrs = f.group(1)
            fid = re.search(r'id="(\d+)"', attrs)
            face = re.search(r'face="([^"]*)"', attrs)
            if not fid or not face:
                continue
            entry = fonts.setdefault(
                int(fid.group(1)),
                {"face": face.group(1), "langs": set(), "embedded": False, "ref": None},
            )
            entry["langs"].add(lang)
            if 'isEmbedded="1"' in attrs:
                entry["embedded"] = True
            bref = re.search(r'binaryItemIDRef="([^"]*)"', attrs)
            if bref:
                entry["ref"] = bref.group(1)

    used_font_ids = set()
    for cid in used_charpr:
        used_font_ids |= charpr_fonts.get(cid, set())

    if installed is None:
        installed = system_fonts()
    known = installed | HANCOM_BUNDLED

    errors: list[str] = []
    warnings: list[str] = []
    report: list[dict] = []
    for fid, e in sorted(fonts.items()):
        if fid not in used_font_ids:
            continue  # 정의만 되고 본문에서 안 쓰는 글꼴은 문제되지 않는다
        face = e["face"]
        if e["embedded"]:
            ok_ref = bool(e["ref"]) and (
                any(e["ref"] in b for b in bindata) or (e["ref"] in hpf)
            )
            status = "embedded" if ok_ref else "embedded-broken"
            if not ok_ref:
                errors.append(
                    f"'{face}': isEmbedded=1인데 binaryItemIDRef가 유효하지 않다 "
                    "(KS X 6101 9.3.2.2.2 — 오류 상황)"
                )
        elif not installed:
            status = "unknown"  # 폰트를 조회할 수 없는 환경
        elif face in known:
            status = "ok"
        else:
            status = "missing"
            warnings.append(
                f"'{face}'가 시스템에 없다 — 한컴이 임의 글꼴로 대체하면 "
                "자간·줄 수가 달라져 쪽 나눔이 밀릴 수 있다"
            )
        report.append({"id": fid, "face": face, "status": status,
                       "langs": sorted(e["langs"])})

    return {
        "fonts": report,
        "errors": errors,
        "warnings": warnings,
        "scanned_system_fonts": len(installed),
    }


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="HWPX 글꼴 사용 점검")
    ap.add_argument("input")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    r = check(a.input)
    if a.json:
        import json

        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(f"시스템 글꼴 {r['scanned_system_fonts']}종 조회")
        for f in r["fonts"]:
            mark = {"ok": "○", "missing": "✕", "embedded": "◆",
                    "embedded-broken": "✕", "unknown": "?"}[f["status"]]
            print(f"  {mark} {f['face']:20s} {f['status']:16s} {','.join(f['langs'])}")
        for e in r["errors"]:
            print(f"  [오류] {e}")
        for w in r["warnings"]:
            print(f"  [주의] {w}")
        if not r["errors"] and not r["warnings"]:
            print("  글꼴 문제 없음")
    sys.exit(1 if r["errors"] else 0)


if __name__ == "__main__":
    main()
