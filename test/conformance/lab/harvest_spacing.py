"""정답본(한/글 재저장) 줄 기록에서 (줄 높이 vertsize, 줄 간격 비율 %, 한/글이 적은 spacing) 을 모아 반올림 규칙을 찾는다.

    python harvest_spacing.py

문단 모양의 lineSpacing 이 PERCENT 이고 한 줄짜리가 아닌 줄 기록만 쓴다(마지막 줄도 spacing 이 적힌다).
"""

import collections
import glob
import math
import re
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ORACLE = Path(__file__).resolve().parent.parent / "out" / "oracle"


def main():
    seen = collections.Counter()
    for f in sorted(glob.glob(str(ORACLE / "*.hwpx"))):
        z = zipfile.ZipFile(f)
        h = z.read("Contents/header.xml").decode("utf-8")
        pct = {}
        for m in re.finditer(r'<hh:paraPr id="(\d+)".*?</hh:paraPr>', h, re.S):
            ls = re.search(r'<hh:lineSpacing type="(\w+)" value="(\d+)"', m.group(0))
            if ls and ls.group(1) == "PERCENT":
                pct[m.group(1)] = int(ls.group(2))
        for n in z.namelist():
            if not re.match(r"Contents/section\d+\.xml$", n):
                continue
            s = z.read(n).decode("utf-8")
            for p in re.finditer(
                r'<hp:p [^>]*paraPrIDRef="(\d+)"[^>]*>(.*?)</hp:p>', s, re.S
            ):
                v = pct.get(p.group(1))
                if not v:
                    continue
                own = re.sub(r"<hp:subList.*?</hp:subList>", "", p.group(2), flags=re.S)
                for seg in re.findall(r"<hp:lineseg ([^>]*)/>", own):
                    a = dict(re.findall(r'(\w+)="(-?\d+)"', seg))
                    seen[(int(a["vertsize"]), v, int(a["spacing"]))] += 1
    rows = []
    for (vs, v, sp), c in seen.items():
        exact = vs * (v - 100) / 100
        if exact <= 0:
            continue
        q = exact / 4
        rows.append(
            (
                vs,
                v,
                sp,
                c,
                exact,
                math.floor(q) * 4,
                math.floor(q + 0.5) * 4,
                q - math.floor(q),
            )
        )
    rule = collections.Counter()
    for vs, v, sp, c, exact, fl, rd, frac in rows:
        k = (
            "내림=반올림"
            if fl == rd == sp
            else "내림"
            if sp == fl
            else "반올림"
            if sp == rd
            else "다름"
        )
        rule[(k, round(frac, 3))] += c
    print("규칙별(소수부) 줄 수:", sorted(rule.items(), key=lambda x: -x[1])[:20])
    print("동점(.5) 사례:")
    for vs, v, sp, c, exact, fl, rd, frac in sorted(rows):
        if abs(frac - 0.5) < 1e-9:
            print(
                f"  높이 {vs} {v}% 정확 {exact} → 한/글 {sp} (내림 {fl}, 반올림 {rd}) {c}줄"
            )
    other = [r for r in rows if r[2] not in (r[5], r[6])]
    print("어느 쪽도 아님:", sorted(other, key=lambda r: -r[3])[:12])


if __name__ == "__main__":
    main()


def check_rules():
    """후보 규칙별로 정답본 줄 기록과 맞는 줄 수."""
    import importlib
    mod = importlib.import_module("harvest_spacing")
    seen = collections.Counter()
    for f in sorted(glob.glob(str(ORACLE / "*.hwpx"))):
        z = zipfile.ZipFile(f)
        h = z.read("Contents/header.xml").decode("utf-8")
        pct = {}
        for m in re.finditer(r'<hh:paraPr id="(\d+)".*?</hh:paraPr>', h, re.S):
            ls = re.search(r'<hh:lineSpacing type="(\w+)" value="(\d+)"', m.group(0))
            if ls and ls.group(1) == "PERCENT":
                pct[m.group(1)] = int(ls.group(2))
        for n in z.namelist():
            if not re.match(r"Contents/section\d+\.xml$", n):
                continue
            s = z.read(n).decode("utf-8")
            for p in re.finditer(r'<hp:p [^>]*paraPrIDRef="(\d+)"[^>]*>(.*?)</hp:p>', s, re.S):
                v = pct.get(p.group(1))
                if not v or v <= 100:
                    continue
                own = re.sub(r"<hp:subList.*?</hp:subList>", "", p.group(2), flags=re.S)
                for seg in re.findall(r"<hp:lineseg ([^>]*)/>", own):
                    a = dict(re.findall(r'(\w+)="(-?\d+)"', seg))
                    seen[(int(a["vertsize"]), v, int(a["spacing"]))] += 1
    rules = {
        "종전: 반올림(h*(p-100)/100/4)*4": lambda h, p: math.floor(h * (p - 100) / 100 / 4 + 0.5) * 4,
        "새: 반올림(내림(h/4)*(p-100)/100)*4": lambda h, p: math.floor((h // 4) * (p - 100) / 100 + 0.5) * 4,
    }
    total = sum(seen.values())
    for name, fn in rules.items():
        ok = sum(c for (h, p, sp), c in seen.items() if fn(h, p) == sp)
        print(f"{name}: {ok}/{total} ({100 * ok / total:.2f}%)")


if __name__ == "__main__" and "--check" in sys.argv:
    check_rules()
