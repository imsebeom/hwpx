"""score.mjs 의 줄바꿈 지표(본문, 칸)를 네이티브 rhwp(claude-linestarts.exe)로 빠르게 낸다. wasm 빌드 없이 엔진 수정 효과를 본다.

    python nativescore.py [정답본 폴더=../out/oracle] [--ids d014,d322] [--out 불일치.jsonl]

차이: 글꼴 파일 폭 등록(font-metrics.mjs)을 하지 않으므로 그 글꼴을 쓰는 문서는 wasm 채점과 다를 수 있다.
같은 엔진의 수정 전후를 견주는 용도다. 칸은 XML 의 「tc 바로 아래 subList」 순서와 엔진의 칸 목록 순서를 맞대며,
칸 수나 칸마다 문단 수가 다르면 그 문서의 칸은 뺀다. 엔진이 [] 를 주는 칸(표 안 표)도 뺀다.
"""

import concurrent.futures as cf
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
EXE = (
    HERE.parents[2]
    / "editor"
    / ".build"
    / "rhwp"
    / "target"
    / "debug"
    / "claude-linestarts.exe"
)
SEG = re.compile(r"<hp:linesegarray>.*?</hp:linesegarray>", re.S)
TOK = re.compile(r"<(/?)hp:([A-Za-z]+)\b([^>]*?)(/?)>")


def parse(xmls):
    """정답본 섹션 XML 들에서 본문 문단과 칸 문단의 줄 시작(score.mjs parseOracle 과 같은 순서)."""
    body, cells = [], []
    for xml in xmls:
        stack = []
        for m in TOK.finditer(xml):
            close, name, attrs, selfc = (
                m.group(1) == "/",
                m.group(2),
                m.group(3),
                m.group(4) == "/",
            )
            if close:
                while stack:
                    if stack.pop()[0] == name:
                        break
                continue
            if name == "p":
                sl = next((e for e in reversed(stack) if e[0] == "subList"), None)
                rec = []
                if sl is None:
                    body.append(rec)
                elif sl[1] >= 0:
                    cells[sl[1]].append(rec)
                if not selfc:
                    stack.append(("p", rec))
                continue
            if name == "subList":
                parent = stack[-1][0] if stack else None
                idx = -1
                if parent == "tc":
                    idx = len(cells)
                    cells.append([])
                if not selfc:
                    stack.append(("subList", idx))
                continue
            if name == "lineseg":
                rec = next((e[1] for e in reversed(stack) if e[0] == "p"), None)
                if rec is not None:
                    tp = re.search(r'\btextpos="(\d+)"', attrs)
                    rec.append(int(tp.group(1)) if tp else 0)
                continue
            if not selfc:
                stack.append((name, None))
    return body, cells


def one(path, tmp):
    z = zipfile.ZipFile(path)
    names = sorted(
        (n for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n)),
        key=lambda n: int(re.findall(r"\d+", n)[-1]),
    )
    xmls = [z.read(n).decode("utf-8") for n in names]
    body, cells = parse(xmls)
    dst = os.path.join(tmp, os.path.basename(path))
    with zipfile.ZipFile(dst, "w") as w:
        for info in z.infolist():
            data = z.read(info.filename)
            if info.filename in names:
                data = SEG.sub("", data.decode("utf-8")).encode("utf-8")
            w.writestr(
                info,
                data,
                compress_type=zipfile.ZIP_STORED
                if info.filename == "mimetype"
                else zipfile.ZIP_DEFLATED,
            )
    r = subprocess.run(
        [str(EXE), dst],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "CLAUDE_CELLS": "1"},
    )
    rb, rc = {}, {}
    pages = None
    for line in r.stdout.splitlines():
        _, key, st = line.split("\t")
        if key == "PAGES":
            pages = int(st)
        elif ":" in key:
            k, p = key.split(":")
            rc.setdefault(int(k), {})[int(p)] = json.loads(st)
        else:
            rb[int(key)] = json.loads(st)
    return os.path.basename(path)[:-5], body, cells, rb, rc, pages


def main():
    args = sys.argv[1:]
    src = (
        args[0]
        if args and not args[0].startswith("--")
        else str(HERE.parent / "out" / "oracle")
    )
    ids = set(args[args.index("--ids") + 1].split(",")) if "--ids" in args else None
    out = args[args.index("--out") + 1] if "--out" in args else None
    files = sorted(glob.glob(os.path.join(src, "*.hwpx")))
    if ids:
        files = [f for f in files if os.path.basename(f)[:-5] in ids]
    tmp = tempfile.mkdtemp(prefix="nativescore_")
    tot = {k: 0 for k in ("bc", "bs", "bm", "bms", "cc", "cs", "cm", "cms", "pc", "ps")}
    page_bad = []
    han_pages = {}
    for line in open(HERE.parent / "out" / "oracle.jsonl", encoding="utf-8"):
        rec = json.loads(line)
        if rec.get("saved") and rec.get("pages"):
            han_pages[rec["id"]] = rec["pages"]
    bad = []
    with cf.ThreadPoolExecutor(8) as ex:
        for name, body, cells, rb, rc, pages in ex.map(lambda f: one(f, tmp), files):
            hp = han_pages.get(name)
            if hp is not None and pages is not None:
                tot["pc"] += 1
                tot["ps"] += pages == hp
                if pages != hp:
                    page_bad.append(f"{name}:{hp}/{pages}")
            if len(rb) == len(body):
                for p, h in enumerate(body):
                    if not h:
                        continue
                    r = rb.get(p, [])
                    ok = r == h
                    tot["bc"] += 1
                    tot["bs"] += ok
                    if len(h) > 1 or len(r) > 1:
                        tot["bm"] += 1
                        tot["bms"] += ok
                    if not ok:
                        bad.append(
                            {
                                "id": name,
                                "where": "본문",
                                "para": p,
                                "han": h,
                                "rhwp": r,
                            }
                        )
            aligned = len(rc) == len(cells) and all(
                len(rc.get(k, {})) == len(c) for k, c in enumerate(cells)
            )
            if aligned:
                for k, c in enumerate(cells):
                    for p, h in enumerate(c):
                        r = rc[k].get(p, [])
                        if not h or not r:
                            continue
                        ok = r == h
                        tot["cc"] += 1
                        tot["cs"] += ok
                        if len(h) > 1 or len(r) > 1:
                            tot["cm"] += 1
                            tot["cms"] += ok
                        if not ok:
                            bad.append(
                                {
                                    "id": name,
                                    "where": "칸",
                                    "cell": k,
                                    "para": p,
                                    "han": h,
                                    "rhwp": r,
                                }
                            )
    pct = lambda a, b: round(100 * a / b, 1) if b else None  # noqa: E731
    print(
        f"문서 {len(files)} | 본문 {pct(tot['bs'], tot['bc'])}% ({tot['bc']}) 여러 줄 {pct(tot['bms'], tot['bm'])}% ({tot['bm']})"
        f" | 칸 {pct(tot['cs'], tot['cc'])}% ({tot['cc']}) 여러 줄 {pct(tot['cms'], tot['cm'])}% ({tot['cm']})"
        f" | 쪽수 {pct(tot['ps'], tot['pc'])}% ({tot['pc']}) | 불일치 {len(bad)}"
    )
    if "--pages" in args:
        print("쪽수 다름(한글/rhwp)", " ".join(sorted(page_bad)))
    if out:
        with open(out, "w", encoding="utf-8") as f:
            for b in bad:
                f.write(json.dumps(b, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
