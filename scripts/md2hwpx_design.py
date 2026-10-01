#!/usr/bin/env python3
"""마크다운 → 디자인 입힌 HWPX (학습지, 평가지, 안내문처럼 한두 쪽짜리 인쇄물용).

md2hwpx.py(report 템플릿)로 조판한 뒤 다음을 입힌다.
  - 첫 `# 제목`  → 강조색 배너(흰 글자, 한 칸 표)
  - `## 절 제목` → 옅은 색 띠 + 왼쪽 굵은 강조색 선, 강조색 글자. 다음 문단과 함께(쪽 끝에 홀로 남지 않음)
  - 표 머리      → 옅은 색 바탕 + 강조색 글자, 표 선은 회색
  - 본문 글꼴    → 맑은 고딕, 본문 문단의 내어쓰기 제거
  - 표 셀의 `<br>` 연쇄 → 쓰기 칸 빈 줄로 살림(md2hwpx 는 빈 줄을 버려 `<br>` 이 글자로 찍힌다)

사용:
    python md2hwpx_design.py 학습지.md -o 학습지.hwpx --theme ink
    python md2hwpx_design.py 학습지.md -o 학습지.hwpx --accent "#1B7F6B" --light "#E3F4EF"

쓰기 칸은 md 표 셀에 `<br>` 를 이어 쓴다: `| 까닭 |\\n| --- |\\n| <br><br><br> |` → 빈 줄 네 줄 높이.
2026-10-01 연구정보원 제출용 학습지 8종에서 다듬은 것을 스크립트로 옮겼다.
"""

import argparse
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

# 강조색, 옅은 색. 옅은 색은 강조색을 흰색에 90% 가까이 섞은 값이다
THEMES = {
    # 기본은 무채색에 가까운 절제된 한 색이다(사용자 선호: 알록달록한 것을 좋아하지 않음)
    "ink": ("#3A3F47", "#F1F2F4"),
    "slate": ("#3D4F63", "#EEF1F4"),
    # 아래는 과목이나 행사를 색으로 구분해 달라는 요청이 있을 때만 쓴다
    "teal": ("#1B7F6B", "#E3F4EF"),
    "orange": ("#C0541A", "#FCEBDD"),
    "purple": ("#4B3F9E", "#ECEAF8"),
    "brown": ("#8A5A2B", "#F5ECE1"),
    "blue": ("#1F5FA8", "#E4EEF9"),
    "red": ("#B23A3A", "#F9E6E6"),
    "green": ("#3E7D2A", "#E9F3E4"),
    "navy": ("#243B5E", "#E6EAF1"),
}
GREY = "#A6A6A6"
ZWSP = "​"  # str.strip() 이 지우지 않는 빈 글자(전각 공백 U+3000 은 지워진다)
SHORT_TABLE_ROWS = (
    15  # 이하면 글자처럼 취급해 본문 순서 고정, 넘으면 쪽에서 나뉘게 둔다
)


NAME_BLANK = "_" * 14  # 이름 쓸 자리. 오른쪽 정렬이라도 이만큼은 비워 둔다


def _is_name_line(ln):
    """학년, 반, 번, 이름을 적는 짧은 줄(표, 제목, 목록이 아닌 것)."""
    t = ln.strip()
    return bool(t) and not t.startswith(("|", "#", "-", "*", ">")) and len(t) <= 60 and re.search(r"이름\s*[:：_]|(학년|반|번|모둠)\W.*이름", t)


def _pad_name_blank(ln):
    """「이름:」 뒤 쓸 자리가 짧거나 없으면 NAME_BLANK 로 채운다(이미 적힌 이름은 그대로)."""
    m = re.search(r"(이름\s*[:：]?\s*)(.*)$", ln)
    tail = m.group(2).strip()
    if tail and not re.fullmatch(r"[_\s　]*", tail):
        return ln
    return ln[: m.start(2)].rstrip() + " " + NAME_BLANK


def preprocess(md: str) -> str:
    out = []
    for ln in md.splitlines():
        m = re.match(r"^(#{1,2}) (.+)$", ln)
        if m:
            mark = "§T" if m.group(1) == "#" else "§H"
            out += ["", f"| {mark} {m.group(2)} |", "| --- |", ""]
            continue
        if _is_name_line(ln):
            out.append("§R " + _pad_name_blank(ln))
            continue
        if ln.lstrip().startswith("|") and "<br" in ln:
            cells = ln.split("|")
            for i, c in enumerate(cells):
                if "<br" in c:
                    parts = re.split(r"<br\s*/?>", c)
                    parts = [p if p.strip() else f" {ZWSP} " for p in parts]
                    cells[i] = "<br>".join(parts)
            ln = "|".join(cells)
        out.append(ln)
    return "\n".join(out)


def _border_fill(i, border, fill=None, left=None):
    def side(tag, col, w="0.12 mm"):
        if col is None:
            return f'<hh:{tag} type="NONE" width="0.1 mm" color="#000000"/>'
        return f'<hh:{tag} type="SOLID" width="{w}" color="{col}"/>'

    lb = side("leftBorder", left, "1.0 mm") if left else side("leftBorder", border)
    fb = (
        f'<hc:fillBrush><hc:winBrush faceColor="{fill}" hatchColor="#999999" alpha="0"/></hc:fillBrush>'
        if fill
        else ""
    )
    return (
        f'<hh:borderFill id="{i}" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">'
        '<hh:slash type="NONE" Crooked="0" isCounter="0"/><hh:backSlash type="NONE" Crooked="0" isCounter="0"/>'
        f"{lb}{side('rightBorder', border)}{side('topBorder', border)}{side('bottomBorder', border)}"
        '<hh:diagonal type="NONE" width="0.1 mm" color="#000000"/>'
        f"{fb}</hh:borderFill>"
    )


def _append(h, list_tag, xml, added):
    """목록 끝에 append 하고 itemCnt 갱신 (규칙 32: 중간 삽입 금지)."""
    h = h.replace(f"</hh:{list_tag}>", xml + f"</hh:{list_tag}>")
    n = int(re.search(rf'<hh:{list_tag} itemCnt="(\d+)"', h).group(1))
    return re.sub(
        rf'<hh:{list_tag} itemCnt="\d+"', f'<hh:{list_tag} itemCnt="{n + added}"', h
    )


def style_header(h, accent, light, font):
    if font:
        h = re.sub(r'face="함초롬(바탕|돋움)"', f'face="{font}"', h)

    n_bf = int(re.search(r'<hh:borderFills itemCnt="(\d+)"', h).group(1))
    ids = {k: n_bf + 1 + i for i, k in enumerate(["banner", "sec", "th", "td"])}
    h = _append(
        h,
        "borderFills",
        _border_fill(ids["banner"], None, accent)
        + _border_fill(ids["sec"], None, light, left=accent)
        + _border_fill(ids["th"], GREY, light)
        + _border_fill(ids["td"], GREY),
        4,
    )

    n_cp = int(re.search(r'<hh:charProperties itemCnt="(\d+)"', h).group(1))

    def clone(src_id, new_id, height, color):
        c = re.search(rf'<hh:charPr id="{src_id}"[\s\S]*?</hh:charPr>', h).group(0)
        c = re.sub(r'id="\d+"', f'id="{new_id}"', c, count=1)
        c = re.sub(r'height="\d+"', f'height="{height}"', c, count=1)
        return re.sub(r'textColor="#[0-9A-Fa-f]+"', f'textColor="{color}"', c, count=1)

    # report 템플릿: 7=20pt 볼드(제목), 8=14pt 볼드(##), 9=10pt 볼드(표 머리)
    cp = {"white": n_cp, "acc": n_cp + 1, "thb": n_cp + 2}
    h = _append(
        h,
        "charProperties",
        clone(7, cp["white"], 1700, "#FFFFFF")
        + clone(8, cp["acc"], 1250, accent)
        + clone(9, cp["thb"], 1000, accent),
        3,
    )

    p0 = re.search(r'<hh:paraPr id="0"[\s\S]*?</hh:paraPr>', h).group(0)
    p0_flat = p0.replace('<hc:intent value="-1000"', '<hc:intent value="0"')
    h = h.replace(p0, p0_flat)
    n_pp = int(re.search(r'<hh:paraProperties itemCnt="(\d+)"', h).group(1))
    keep = re.sub(r'id="0"', f'id="{n_pp}"', p0_flat, count=1).replace(
        'keepWithNext="0"', 'keepWithNext="1"'
    )
    right = re.sub(r'id="0"', f'id="{n_pp + 1}"', p0_flat, count=1).replace('horizontal="JUSTIFY"', 'horizontal="RIGHT"')
    h = _append(h, "paraProperties", keep + right, 2)
    cp["keep_pp"] = n_pp
    cp["right_pp"] = n_pp + 1
    return h, ids, cp


def _set_attr(tag, name, value):
    if f'{name}="' in tag:
        return re.sub(rf'{name}="[^"]*"', f'{name}="{value}"', tag, count=1)
    return tag[:-1] + f' {name}="{value}">'


def style_section(s, ids, cp):
    # 표 배치: 짧은 표는 글자처럼 취급 + 나누지 않음(treatAsChar=0 + NONE 이면 표가 뒤 절보다 늦게 떠서 순서가 뒤바뀐다).
    # 긴 표는 규칙 33에 따라 treatAsChar=0 을 지키고 셀 단위가 아닌 표 단위로 나누며 머리 행을 반복한다.
    def place(m):
        t = m.group(0)
        head = re.match(r"<hp:tbl\b[^>]*>", t).group(0)
        rows = int(re.search(r'rowCnt="(\d+)"', head).group(1))
        if rows <= SHORT_TABLE_ROWS:
            new_head = _set_attr(head, "pageBreak", "NONE")
            t = new_head + t[len(head) :]
            t = re.sub(
                r'(<hp:pos\b[^>]*?)treatAsChar="0"', r'\1treatAsChar="1"', t, count=1
            )
        else:
            new_head = _set_attr(
                _set_attr(head, "pageBreak", "TABLE"), "repeatHeader", "1"
            )
            t = new_head + t[len(head) :]
        return t

    s = re.sub(r"<hp:tbl\b[\s\S]*?</hp:tbl>", place, s)

    pid = 990000
    empty = '<hp:p id="{}" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="11"><hp:t/></hp:run></hp:p>'
    for mark in ("§H ", "§T "):
        pos = len(s)
        while True:
            pos = s.rfind(mark, 0, pos)
            if pos < 0:
                break
            p0 = s.rfind("<hp:p ", 0, s.rfind("<hp:tbl", 0, pos))
            after = s.find("</hp:p>", s.find("</hp:tbl>", pos)) + 7
            pid += 1
            if mark == "§T ":
                s = s[:after] + empty.format(pid) + s[after:]
                continue
            # 절 제목 문단과, 바로 뒤가 표가 아닌 일반 문단이면 그것까지 다음 문단과 함께
            q0 = s.find("<hp:p ", after)
            q1 = s.find("</hp:p>", q0)
            if q0 > 0 and "<hp:tbl" not in s[q0:q1]:
                qe = s.find(">", q0)
                if 'paraPrIDRef="0"' in s[q0:qe]:
                    s = (
                        s[:q0]
                        + s[q0:qe].replace(
                            'paraPrIDRef="0"', f'paraPrIDRef="{cp["keep_pp"]}"'
                        )
                        + s[qe:]
                    )
            pe = s.find(">", p0)
            ptag = re.sub(
                r'paraPrIDRef="\d+"',
                f'paraPrIDRef="{cp["keep_pp"]}"',
                s[p0:pe],
                count=1,
            )
            s = s[:p0] + empty.format(pid) + ptag + s[pe:]

    def bf(x, v):
        return re.sub(
            r'(<hp:tc\b[^>]*?)borderFillIDRef="\d+"', rf'\1borderFillIDRef="{v}"', x
        )

    name_ids = iter(range(980000, 989999))

    def fix_name(m):
        p = m.group(0).replace("§R ", "", 1)
        p = re.sub(r'paraPrIDRef="\d+"', f'paraPrIDRef="{cp["right_pp"]}"', p, count=1)
        return p + empty.format(next(name_ids))  # 이름 줄 아래 한 줄 비움(사용자 확인)

    s = re.sub(r"<hp:p (?:(?!<hp:p )[\s\S])*?§R [\s\S]*?</hp:p>", fix_name, s)

    def fix_tbl(m):
        t = m.group(0)
        kind = "T" if "§T " in t else "H" if "§H " in t else None
        if kind == "T":
            t = bf(t.replace("§T ", ""), ids["banner"])
            t = re.sub(r'charPrIDRef="\d+"', f'charPrIDRef="{cp["white"]}"', t)
            t = re.sub(r'(<hp:cellSz width="\d+" height=")\d+', r"\g<1>3400", t)
            return re.sub(
                r'(<hp:cellMargin left=")\d+(" right=")\d+(" top=")\d+(" bottom=")\d+',
                r"\g<1>850\g<2>850\g<3>425\g<4>425",
                t,
            )
        if kind == "H":
            t = bf(t.replace("§H ", ""), ids["sec"])
            t = re.sub(r'charPrIDRef="\d+"', f'charPrIDRef="{cp["acc"]}"', t)
            t = t.replace('paraPrIDRef="21"', 'paraPrIDRef="22"')  # 가운데 → 왼쪽
            return re.sub(r'(<hp:cellMargin left=")\d+', r"\g<1>567", t)

        def fix_tc(c):
            x = c.group(0)
            if 'header="1"' in x:
                return bf(x, ids["th"]).replace(
                    'charPrIDRef="9"', f'charPrIDRef="{cp["thb"]}"'
                )
            return bf(x, ids["td"])

        return re.sub(r"<hp:tc\b[\s\S]*?</hp:tc>", fix_tc, t)

    return re.sub(r"<hp:tbl\b[\s\S]*?</hp:tbl>", fix_tbl, s)


def build(md_path, out, accent, light, font="Pretendard", layout=True):
    md_path, out = Path(md_path).resolve(), Path(out).resolve()
    tmp_md = out.with_name(out.stem + ".__pre.md")
    tmp_md.write_text(preprocess(md_path.read_text(encoding="utf-8")), encoding="utf-8")
    try:
        r = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_DIR / "md2hwpx.py"),
                str(tmp_md),
                "--template",
                "report",
                "--output",
                str(out),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if r.returncode != 0:
            sys.exit(f"md2hwpx 실패:\n{r.stdout}\n{r.stderr}")
    finally:
        tmp_md.unlink(missing_ok=True)

    with zipfile.ZipFile(out) as z:
        h = z.read("Contents/header.xml").decode("utf-8")
        s = z.read("Contents/section0.xml").decode("utf-8")
    h, ids, cp = style_header(h, accent, light, font)
    s = style_section(s, ids, cp)
    tmp = str(out) + ".tmp"
    with (
        zipfile.ZipFile(out) as zi,
        zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo,
    ):
        for it in zi.infolist():
            d = zi.read(it.filename)
            if it.filename == "Contents/header.xml":
                d = h.encode("utf-8")
            elif it.filename == "Contents/section0.xml":
                d = s.encode("utf-8")
            zo.writestr(it, d)  # 원본 ZipInfo 로 mimetype, version.xml 의 STORED 보존
    os.replace(tmp, out)

    fix = [sys.executable, str(SCRIPT_DIR / "fix_namespaces.py"), str(out)]
    if not layout:
        fix.append("--no-layout")
    subprocess.run(fix, check=True, capture_output=True)
    v = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "validate.py"), str(out)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    print(
        f"{out.name}: {v.stdout.strip().splitlines()[-1].strip() if v.stdout.strip() else v.returncode}"
    )
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("input")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--theme", choices=sorted(THEMES), default="ink")
    ap.add_argument("--accent", help="강조색 #RRGGBB (주면 --theme 대신)")
    ap.add_argument("--light", help="옅은 색 #RRGGBB (--accent 와 함께)")
    ap.add_argument(
        "--font", default="Pretendard", help="본문 글꼴(기본 Pretendard, 스킬 fonts/ 에 동봉). 빈 문자열이면 템플릿 글꼴 유지"
    )
    ap.add_argument(
        "--no-layout",
        action="store_true",
        help="한글(COM) 줄 배치 생략 (한글 없는 환경)",
    )
    a = ap.parse_args()
    accent, light = THEMES[a.theme]
    if a.accent:
        accent, light = a.accent, a.light or light
    build(a.input, a.output, accent, light, a.font or None, layout=not a.no_layout)


if __name__ == "__main__":
    main()
