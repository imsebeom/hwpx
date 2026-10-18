"""문단 기준 위아래 배치(글자처럼 취급 아님) 표가 남은 자리에 안 들어갈 때 한/글이 그 쪽에 넘쳐 두는지, 다음 쪽으로 넘기는지 센다.

    python harvest_overflowtbl.py

본문 높이 = 용지 높이 - 위아래 여백 - 머리말, 꼬리말. 표 문단 vpos + 오프셋 + 바깥 여백 + 표 높이가 본문 높이를 넘는데 vpos > 0 이면 「넘쳐 둠」,
vpos == 0 이고 앞 문단 끝 + 표 높이가 본문 높이를 넘으면 「넘김」. 나눔 설정(pageBreak), 표 높이가 본문의 몇 %인지, 문단에 글이 있는지로 나눈다.
"""

import collections
import glob
import os
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")

stat = collections.Counter()
ex = collections.defaultdict(list)
for path in sorted(glob.glob("../out/oracle/*.hwpx")):
    doc = os.path.basename(path)[:-5]
    z = zipfile.ZipFile(path)
    for name in sorted(
        n for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n)
    ):
        s = z.read(name).decode("utf-8")
        pp = re.search(
            r'<hp:pagePr [^>]*height="(\d+)".*?<hp:margin header="(\d+)" footer="(\d+)" gutter="\d+" left="\d+" right="\d+" top="(\d+)" bottom="(\d+)"',
            s,
            re.S,
        )
        if not pp:
            continue
        body = int(pp.group(1)) - sum(int(pp.group(i)) for i in (2, 3, 4, 5))
        paras = []
        depth, start = 0, -1
        for m in re.finditer(r"<(/?)hp:(p|subList)\b[^>]*?(/?)>", s):
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
                paras.append(s[start : m.end()])
                start = -1
        prev_end = None
        for p in paras:
            own = re.sub(r"<hp:subList\b.*?</hp:subList>", "", p, flags=re.S)
            segs = re.findall(
                r'<hp:lineseg textpos="\d+" vertpos="(-?\d+)" vertsize="(\d+)" textheight="\d+" baseline="\d+" spacing="(-?\d+)"',
                own,
            )
            tb = re.search(
                r'<hp:tbl [^>]*textWrap="TOP_AND_BOTTOM"[^>]*pageBreak="(\w+)"[^>]*>.*?<hp:sz [^>]*height="(\d+)".*?<hp:pos ([^>]*)>.*?<hp:outMargin [^>]*top="(\d+)" bottom="(\d+)"',
                own,
                re.S,
            )
            if (
                segs
                and tb
                and 'treatAsChar="0"' in tb.group(3)
                and 'vertRelTo="PARA"' in tb.group(3)
            ):
                v = int(segs[0][0])
                h = int(tb.group(2))
                voff = int(re.search(r'vertOffset="(-?\d+)"', tb.group(3)).group(1))
                need = max(voff, 0) + int(tb.group(4)) + h + int(tb.group(5))
                text = bool(re.search(r"<hp:t>[^<]", own))
                ratio = "본문 절반 이상" if h > body / 2 else "본문 절반 미만"
                # 용지 바닥까지 남은 높이(아래 여백 + 꼬리말)
                paper_room = int(pp.group(3)) + int(pp.group(5))
                if v > 0 and v + need > body:
                    key = (
                        "넘쳐 둠",
                        tb.group(1),
                        ratio,
                        "글 있음" if text else "글 없음",
                    )
                    stat[key] += 1
                    if len(ex[key]) < 4:
                        ex[key].append(
                            f"{doc} v={v} need={need} body={body} 넘침={v + need - body} 바닥여유={paper_room}"
                        )
                elif (
                    v == 0
                    and prev_end is not None
                    and prev_end + need > body
                    and h < body
                ):
                    key = ("넘김", tb.group(1), ratio, "글 있음" if text else "글 없음")
                    stat[key] += 1
                    if len(ex[key]) < 4:
                        ex[key].append(
                            f"{doc} 앞 끝={prev_end} need={need} body={body} 넘칠 양={prev_end + need - body} 바닥여유={paper_room}"
                        )
            if segs:
                last = segs[-1]
                prev_end = int(last[0]) + int(last[1]) + int(last[2])
for k, n in sorted(stat.items()):
    print(n, k, ex[k])
