"""정답본(한/글 재저장) 줄 기록에서 글꼴마다 「줄 높이(vertsize) ÷ 글자 크기」를 모은다.

    python harvest_lineheight.py

run 이 하나뿐이고 글자처럼 취급 개체가 없는 문단만 쓴다. 한글 글꼴과 라틴 글꼴이 같은 글자 모양만 센다.
"""

import collections
import glob
import re
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ORACLE = Path(__file__).resolve().parent.parent / "out" / "oracle"


def main():
    ratios = collections.defaultdict(collections.Counter)
    for f in sorted(glob.glob(str(ORACLE / "*.hwpx"))):
        z = zipfile.ZipFile(f)
        h = z.read("Contents/header.xml").decode("utf-8")
        faces = {}
        for lang in ("HANGUL", "LATIN"):
            b = re.search(rf'<hh:fontface lang="{lang}".*?</hh:fontface>', h, re.S).group(0)
            faces[lang] = dict(re.findall(r'<hh:font id="(\d+)" face="([^"]+)"', b))
        cps = {}
        for m in re.finditer(r'<hh:charPr id="(\d+)" height="(\d+)".*?</hh:charPr>', h, re.S):
            fr = re.search(r'<hh:fontRef hangul="(\d+)" latin="(\d+)"', m.group(0)).groups()
            rel = re.search(r'<hh:relSz hangul="(\d+)" latin="(\d+)"', m.group(0)).groups()
            hf, lf = faces["HANGUL"].get(fr[0]), faces["LATIN"].get(fr[1])
            if hf and hf == lf and rel == ("100", "100"):
                cps[m.group(1)] = (hf, int(m.group(2)))
        for n in z.namelist():
            if not re.match(r"Contents/section\d+\.xml$", n):
                continue
            s = z.read(n).decode("utf-8")
            for p in re.finditer(r"<hp:p [^>]*>(.*?)</hp:p>", s, re.S):
                body = re.sub(r"<hp:subList.*?</hp:subList>", "", p.group(1), flags=re.S)
                runs = re.findall(r'<hp:run charPrIDRef="(\d+)"', body)
                if len(set(runs)) != 1 or runs[0] not in cps or "<hp:ctrl" in body or "<hp:tbl" in body or "<hp:pic" in body:
                    continue
                if not re.search(r"<hp:t>[^<]", body):
                    continue
                face, size = cps[runs[0]]
                for seg in re.findall(r'<hp:lineseg [^>]*vertsize="(\d+)"', body)[:1]:
                    ratios[face][round(int(seg) / size, 3)] += 1
    for face, c in sorted(ratios.items(), key=lambda x: -sum(x[1].values())):
        tot = sum(c.values())
        print(f"{face:20s} {tot:6d}  {c.most_common(3)}")


if __name__ == "__main__":
    main()
