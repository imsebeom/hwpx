"""정답본에서 채점기 칸 번호(nativescore 의 cell 순서)에 해당하는 칸의 XML 요약을 찍는다.

    python showcell.py <id> <칸 번호>...

칸 크기, 여백, 문단마다 글과 한/글 줄 기록(textpos, horzsize), 그 칸이 든 표의 열 수와 크기를 보인다.
"""

import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
doc = sys.argv[1]
want = {int(x) for x in sys.argv[2:]}
z = zipfile.ZipFile(f"../out/oracle/{doc}.hwpx")
names = sorted(
    (n for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n)),
    key=lambda n: int(re.findall(r"\d+", n)[-1]),
)
idx = 0
for n in names:
    s = z.read(n).decode("utf-8")
    # 칸 번호 = <hp:tc> 바로 아래 subList 가 나오는 순서
    for m in re.finditer(r"<hp:tc\b[^>]*>\s*<hp:subList\b", s):
        if idx in want:
            tc_end = s.find("</hp:tc>", m.start())
            # 중첩 표가 있으면 끝을 바깥 tc 의 끝으로 맞춘다
            depth = 0
            for t in re.finditer(r"<(/?)hp:tc\b", s[m.start() :]):
                depth += -1 if t.group(1) else 1
                if depth == 0:
                    tc_end = m.start() + t.start()
                    break
            tc = s[m.start() : tc_end]
            tbl0 = s.rfind("<hp:tbl ", 0, m.start())
            tbl = re.search(r"<hp:tbl [^>]*>", s[tbl0:]).group(0)
            print(
                f"== 칸 {idx}",
                re.search(r'colCnt="\d+"', tbl).group(0),
                re.search(r'rowCnt="\d+"', tbl).group(0),
                re.search(r"<hp:sz [^>]*>", s[tbl0:]).group(0),
            )
            print(
                "  ",
                re.search(r"<hp:cellAddr[^>]*>", tc).group(0)
                if re.search(r"<hp:cellAddr[^>]*>", tc)
                else "",
                re.search(r"<hp:cellSpan[^>]*>", tc).group(0)
                if re.search(r"<hp:cellSpan[^>]*>", tc)
                else "",
                re.search(r"<hp:cellSz[^>]*>", tc).group(0)
                if re.search(r"<hp:cellSz[^>]*>", tc)
                else "",
                re.search(r"<hp:cellMargin[^>]*>", tc).group(0)
                if re.search(r"<hp:cellMargin[^>]*>", tc)
                else "",
                re.search(r'hasMargin="\d"', tc).group(0)
                if re.search(r'hasMargin="\d"', tc)
                else "",
            )
            for p in re.findall(r"<hp:p [^>]*>.*?</hp:p>", tc, re.S)[:4]:
                text = "".join(re.findall(r"<hp:t>([^<]*)", p))[:60]
                segs = re.findall(
                    r'textpos="(\d+)"[^>]*horzpos="(-?\d+)" horzsize="(\d+)"', p
                )
                print(
                    "   ",
                    repr(text),
                    segs[:6],
                    re.search(r'paraPrIDRef="\d+"', p).group(0),
                    re.findall(r'charPrIDRef="(\d+)"', p)[:3],
                )
        idx += 1
