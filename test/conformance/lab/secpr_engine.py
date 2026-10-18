"""첫 run 이 구역 정의(secPr)만 담은 본문 문단(첫 구역 앞 3문단)에서 엔진 첫 줄 높이/간격이 한/글 줄 기록과 맞는지 센다.

    python secpr_engine.py [--list]

어긋난 문단은 run 마다 (글자 모양 크기, 내용 종류)를 함께 찍는다. 종류: secPr, 글, 표, 그림 등과 글자처럼 취급(TAC) 여부.
"""

import collections
import glob
import os
import re
import subprocess
import sys
import tempfile
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
from segcmp import EXE, HERE, SEG, top_paras  # noqa: E402


def kinds(run_xml):
    top = re.sub(r"<hp:subList\b.*?</hp:subList>", "", run_xml, flags=re.S)
    out = []
    if "<hp:secPr" in top:
        out.append("secPr")
    if re.search(r"<hp:t>[^<]", top):
        out.append("글")
    for m in re.finditer(r"<hp:(tbl|pic|equation|container|rect|line|ellipse)\b", top):
        tail = top[m.start() : m.start() + 3000]
        tac = re.search(r'treatAsChar="(\d)"', tail)
        aff = re.search(r'affectLSpacing="(\d)"', tail)
        out.append(
            f"{m.group(1)}{'@' if tac and tac.group(1) == '1' else ''}{'+' if aff and aff.group(1) == '1' else ''}"
        )
    return out


def main():
    stat = collections.Counter()
    rows = []
    for path in sorted(glob.glob(str(HERE.parent / "out" / "oracle" / "*.hwpx"))):
        doc = os.path.basename(path)[:-5]
        z = zipfile.ZipFile(path)
        h = z.read("Contents/header.xml").decode("utf-8", "replace")
        size = dict(re.findall(r'<hh:charPr id="(\d+)" height="(\d+)"', h))
        sec = z.read("Contents/section0.xml").decode("utf-8")
        # 첫 3문단 원문(최상위)
        paras = []
        depth, start = 0, -1
        for m in re.finditer(r"<(/?)hp:(p|subList)\b[^>]*?(/?)>", sec):
            close, selfc = m.group(1) == "/", m.group(3) == "/"
            if m.group(2) == "subList":
                if not selfc:
                    depth += -1 if close else 1
                continue
            if depth:
                continue
            if not close and not selfc:
                start = m.start()
            elif close and start >= 0:
                paras.append(sec[start : m.end()])
                start = -1
                if len(paras) >= 3:
                    break
        targets = []
        for i, p in enumerate(paras):
            body = SEG.sub("", p)
            runs = []
            pos = 0
            # 최상위 run 만: 칸 안을 지운 뒤 run 경계를 찾는다
            flat = re.sub(
                r"<hp:subList\b.*?</hp:subList>", "<hp:subList/>", body, flags=re.S
            )
            for m in re.finditer(
                r'<hp:run charPrIDRef="(\d+)"(/>|>(.*?)</hp:run>)', flat, re.S
            ):
                runs.append((int(size.get(m.group(1), 0)), kinds(m.group(3) or "")))
            if runs and runs[0][1] == ["secPr"] and len(runs) > 1:
                targets.append((i, runs))
            pos += 1
        if not targets:
            continue
        han = top_paras(sec)
        tmp = tempfile.mkdtemp()
        dst = os.path.join(tmp, f"{doc}.hwpx")
        with zipfile.ZipFile(dst, "w") as w:
            for info in z.infolist():
                data = z.read(info.filename)
                if re.match(r"Contents/section\d+\.xml$", info.filename):
                    data = SEG.sub("", data.decode("utf-8")).encode("utf-8")
                w.writestr(info, data)
        r = subprocess.run(
            [str(EXE), dst],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={
                **os.environ,
                "CLAUDE_SEGV": "1",
                "CLAUDE_METRICS_DIR": str(HERE.parent / "out" / "metrics"),
            },
        )
        eng = {}
        for line in r.stderr.splitlines():
            if line.startswith("SEGV "):
                parts = line.split()
                eng[int(parts[1])] = [
                    tuple(int(x) for x in s.split("/")[1:]) for s in parts[2:]
                ]
        for i, runs in targets:
            if i >= len(han) or not han[i] or not eng.get(i):
                continue
            hv, hs = han[i][0]
            ev, es = eng[i][0]
            ok = abs(hv - ev) <= 2 and abs(hs - es) <= 4
            shape = tuple((s, tuple(k)) for s, k in runs)
            stat[("같음" if ok else "다름")] += 1
            if not ok:
                rows.append(f"{doc} p{i} 한/글 {hv}/{hs} 엔진 {ev}/{es} runs {shape}")
    print(dict(stat))
    for row in rows:
        print(" ", row)


if __name__ == "__main__":
    main()
