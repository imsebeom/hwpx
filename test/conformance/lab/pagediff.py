"""쪽이 처음 어긋나는 본문 문단과 그 앞뒤를 찍는다(한/글 쪽은 정답본 vertpos 되감기, rhwp 쪽은 getPageOfPosition).

python pagediff.py <id>...
"""

import os
import re
import sys
import tempfile
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nativescore import HERE, one  # noqa: E402

SEG = re.compile(r"<hp:linesegarray>.*?</hp:linesegarray>", re.S)


def body_xml(path):
    """본문 문단(최상위)의 원문과 첫 줄 vertpos, 줄 높이 정보."""
    z = zipfile.ZipFile(path)
    names = sorted(
        (n for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n)),
        key=lambda n: int(re.findall(r"\d+", n)[-1]),
    )
    out = []
    for n in names:
        xml = z.read(n).decode("utf-8")
        depth, start = 0, None
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


def main():
    tmp = tempfile.mkdtemp(prefix="pagediff_")
    for doc in sys.argv[1:]:
        path = str(HERE.parent / "out" / "oracle" / f"{doc}.hwpx")
        _, body, _, _, _, (pages, para_pages, han_bp) = one(path, tmp)
        paras = body_xml(path)
        # 문단 안에서 쪽이 넘어가는 경우(줄 vertpos 되감김)도 세어 한/글 쪽을 다시 매긴다(채점기는 문단 첫 줄만 본다)
        han_bp, page, prev = [], 0, -1
        for p in paras:
            segs = SEG.findall(p)
            vs = (
                [int(x) for x in re.findall(r'vertpos="(-?\d+)"', segs[-1])]
                if segs
                else []
            )
            first_page = None
            # 쪽 나눔 표시(pageBreak="1")가 있는 문단은 앞 문단이 vpos 0 에서 끝나도(한 줄짜리 표 문단 등) 새 쪽이다
            forced = (
                prev >= 0 and re.match(r'<hp:p\b[^>]*\bpageBreak="1"', p) is not None
            )
            for v in vs:
                if prev >= 0 and (v < prev or forced):
                    forced = False
                    page += 1
                prev = v
                if first_page is None:
                    first_page = page
            han_bp.append(first_page if first_page is not None else page)
        first = next(
            (i for i, (a, b) in enumerate(zip(para_pages, han_bp)) if a != b), None
        )
        print(
            f"== {doc} 쪽수 rhwp {pages} / 한글 {han_bp[-1] + 1 if han_bp else '?'}  처음 어긋난 문단 {first}"
        )
        if first is None:
            continue
        for i in range(max(0, first - 3), min(len(paras), first + 2)):
            p = paras[i]
            segs = SEG.findall(p)
            v = re.findall(r'vertpos="(-?\d+)"', segs[-1]) if segs else []
            h = re.findall(r'vertsize="(\d+)"', segs[-1]) if segs else []
            ctrls = sorted(
                set(
                    re.findall(
                        r"<hp:(tbl|pic|rect|equation|container|line|ellipse|ole|colPr|secPr|pageBreak)\b",
                        SEG.sub("", p),
                    )
                )
            )
            pb = (
                re.search(r'pageBreak="(\d)"', p).group(1)
                if re.search(r'pageBreak="(\d)"', p)
                else "?"
            )
            txt = "".join(re.findall(r"<hp:t>([^<]*)</hp:t>", SEG.sub("", p)))[:30]
            print(
                f"  p{i} 쪽 한글 {han_bp[i]} rhwp {para_pages[i] if i < len(para_pages) else '?'} | vertpos {v[:1]}~{v[-1:]} 줄높이 {h[:1]} 줄 {len(v)} | 쪽나눔 {pb} | {ctrls} | {txt!r}"
            )


if __name__ == "__main__":
    main()
