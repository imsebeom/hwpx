"""nativescore 와 같은 번호(칸 k, 문단 p)로 정답본의 칸 문단을 찾아 글, 줄 배치, 문단 여백, 칸 폭과 여백을 찍는다.

python cellpara.py <id> <k> <p>
"""

import re
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ORACLE = Path(__file__).resolve().parent.parent / "out" / "oracle"
TOK = re.compile(r"<(/?)hp:([A-Za-z]+)\b([^>]*?)(/?)>")


def main():
    doc, k_want, p_want = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    z = zipfile.ZipFile(ORACLE / f"{doc}.hwpx")
    h = z.read("Contents/header.xml").decode()
    names = sorted(
        (n for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n)),
        key=lambda n: int(re.findall(r"\d+", n)[-1]),
    )
    ncell = -1
    for n in names:
        xml = z.read(n).decode()
        stack = []  # (이름, 시작 위치, 칸 번호, 문단 수 상자)
        for m in TOK.finditer(xml):
            close, name, selfc = m.group(1) == "/", m.group(2), m.group(4) == "/"
            if close:
                while stack:
                    e = stack.pop()
                    if e[0] == name:
                        if name == "p" and e[2] is not None:
                            k, p = e[2]
                            if (k, p) == (k_want, p_want):
                                show(xml, h, e[1], m.end(), stack)
                                return
                        break
                continue
            if name == "subList":
                cell = None
                if stack and stack[-1][0] == "tc":
                    ncell += 1
                    cell = [ncell, 0]
                if not selfc:
                    stack.append(("subList", m.start(), cell))
                continue
            if name == "p":
                sl = next((e for e in reversed(stack) if e[0] == "subList"), None)
                key = None
                if sl is not None and sl[2] is not None:
                    key = (sl[2][0], sl[2][1])
                    sl[2][1] += 1
                if not selfc:
                    stack.append(("p", m.start(), key))
                continue
            if not selfc:
                stack.append((name, m.start(), None))
    print("못 찾음")


def show(xml, header, start, end, stack):
    p = xml[start:end]
    own = re.sub(r"<hp:subList.*?</hp:subList>", "", p, flags=re.S)
    print("글", "".join(re.findall(r"<hp:t>([^<]*)</hp:t>", own))[:100])
    segs = re.findall(r"<hp:linesegarray>(.*?)</hp:linesegarray>", own, re.S)
    print(
        "줄",
        [
            dict(re.findall(r'(textpos|horzpos|horzsize)="(-?\d+)"', x))
            for x in re.findall(r"<hp:lineseg [^>]*>", segs[-1] if segs else "")
        ],
    )
    faces = {
        lang: dict(
            re.findall(
                r'<hh:font id="(\d+)" face="([^"]+)"',
                re.search(
                    rf'<hh:fontface lang="{lang}".*?</hh:fontface>', header, re.S
                ).group(0),
            )
        )
        for lang in ("HANGUL", "LATIN", "SYMBOL")
    }
    for cp in dict.fromkeys(re.findall(r'charPrIDRef="(\d+)"', own)):
        c = re.search(rf'<hh:charPr id="{cp}".*?</hh:charPr>', header, re.S).group(0)
        fr = dict(
            re.findall(
                r'(hangul|latin|symbol)="(\d+)"',
                re.search(r"<hh:fontRef [^>]*>", c).group(0),
            )
        )
        ratio = re.search(r'<hh:ratio hangul="(\d+)"', c).group(1)
        spacing = re.search(r'<hh:spacing hangul="(-?\d+)"', c).group(1)
        print(
            f"글자 모양 {cp}: 크기 {re.search(r'height=\"(\d+)\"', c).group(1)} 한글 {faces['HANGUL'].get(fr['hangul'])} 라틴 {faces['LATIN'].get(fr['latin'])}"
            f" 기호 {faces['SYMBOL'].get(fr['symbol'])} 장평 {ratio} 자간 {spacing} {re.search(r'useFontSpace=\"(\d)\"', c).group(0)}"
            f"{' 굵게' if '<hh:bold/>' in c else ''}"
        )
    pp = re.search(r'paraPrIDRef="(\d+)"', p).group(1)
    mg = re.search(
        rf'<hh:paraPr id="{pp}".*?<hh:margin>(.*?)</hh:margin>', header, re.S
    ).group(1)
    print("문단 여백", dict(re.findall(r'<hc:(\w+) value="(-?\d+)"', mg)))
    tc = next(e for e in reversed(stack) if e[0] == "tc")
    tc_xml = xml[tc[1] : xml.find("<hp:subList", tc[1])]
    tail = xml[xml.find("</hp:subList>", tc[1]) : xml.find("</hp:tc>", tc[1])]
    print(
        "칸",
        re.search(r'hasMargin="\d"', tc_xml).group(0),
        re.findall(r"<hp:cellSz[^>]*>|<hp:cellMargin[^>]*>", tail),
    )
    tbl = xml.rfind("<hp:tbl ", 0, tc[1])
    print("표", re.search(r"<hp:inMargin[^>]*>", xml[tbl : tbl + 3000]).group(0))


if __name__ == "__main__":
    main()
