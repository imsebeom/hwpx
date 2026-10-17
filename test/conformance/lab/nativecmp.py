"""한/글 재저장본 폴더의 본문 문단 줄 시작을 네이티브 rhwp(claude-linestarts.exe)와 맞대어 본다. wasm 빌드 없이 확인용.

python nativecmp.py <한/글 재저장 폴더> [--show]
"""

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
EXE = (
    Path(__file__).resolve().parents[3]
    / "editor"
    / ".build"
    / "rhwp"
    / "target"
    / "debug"
    / "claude-linestarts.exe"
)
SEG = re.compile(r"<hp:linesegarray>.*?</hp:linesegarray>", re.S)


def body_paras(xml):
    """최상위 문단(칸, 글상자 안 문단 제외)의 원문 목록."""
    out, depth, start = [], 0, None
    for m in re.finditer(r"<(/?)hp:(p|subList)\b[^>]*?(/?)>", xml):
        close, name, selfc = m.group(1) == "/", m.group(2), m.group(3) == "/"
        if name == "subList":
            if not selfc:
                depth += -1 if close else 1
            continue
        if depth:
            continue
        if not close and not selfc:
            start = m.start()
        elif close and start is not None:
            out.append(xml[start : m.end()])
            start = None
    return out


def cut(t, starts, off):
    """줄 시작 목록으로 글을 줄마다 나눠 「 | 」로 잇는다. off 는 첫 문단 앞 조판 부호 몫."""
    return " | ".join(
        t[max(0, a - off) : (b - off if b else None)]
        for a, b in zip(starts, starts[1:] + [None])
    )


def main():
    src = sys.argv[1]
    show = "--show" in sys.argv
    tmp = tempfile.mkdtemp(prefix="nativecmp_")
    han, texts, files = {}, {}, []
    for f in sorted(glob.glob(os.path.join(src, "*.hwpx"))):
        name = os.path.basename(f)[:-5]
        z = zipfile.ZipFile(f)
        dst = os.path.join(tmp, name + ".hwpx")
        with zipfile.ZipFile(dst, "w") as w:
            for info in z.infolist():
                data = z.read(info.filename)
                if re.match(r"Contents/section\d+\.xml$", info.filename):
                    xml = data.decode("utf-8")
                    paras = body_paras(xml)
                    han.setdefault(name, []).extend(
                        [
                            int(x)
                            for x in re.findall(
                                r'<hp:lineseg\b[^>]*\btextpos="(\d+)"',
                                SEG.findall(p)[-1],
                            )
                        ]
                        if SEG.findall(p)
                        else []
                        for p in paras
                    )
                    texts.setdefault(name, []).extend(
                        "".join(re.findall(r"<hp:t>([^<]*)</hp:t>", SEG.sub("", p)))
                        for p in paras
                    )
                    data = SEG.sub("", xml).encode("utf-8")
                w.writestr(
                    info,
                    data,
                    compress_type=zipfile.ZIP_STORED
                    if info.filename == "mimetype"
                    else zipfile.ZIP_DEFLATED,
                )
        files.append(dst)
    out = subprocess.run(
        [str(EXE), *files], capture_output=True, text=True, encoding="utf-8"
    ).stdout
    rh = {}
    for line in out.splitlines():
        path, p, st = line.split("\t")
        rh.setdefault(os.path.basename(path)[:-5], {})[int(p)] = json.loads(st)
    same = total = 0
    for name in han:
        bad = []
        for p, h in enumerate(han[name]):
            if not h:
                continue
            r = rh.get(name, {}).get(p)
            total += 1
            if r == h:
                same += 1
            else:
                bad.append((p, h, r))
        print(
            f"{name} {'같음' if not bad else '다름'} "
            + " ".join(f"p{p} 한글{h} rhwp{r}" for p, h, r in bad)
        )
        if show:
            for p, h, r in bad:
                off = 16 if p == 0 else 0
                t = texts[name][p]
                print("   한글", cut(t, h, off))
                print("   rhwp", cut(t, r or [], off))
    print(f"문단 {same}/{total} 같음")


if __name__ == "__main__":
    main()
