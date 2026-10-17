"""불일치(nativescore --out) 를 글꼴과 방향으로 묶는다.

    python mmstat.py <불일치.jsonl>

방향: rhwp 가 먼저 꺾음(rhwp 줄 시작이 한/글보다 앞 = rhwp 가 넓게 잼), 늦게 꺾음(좁게 잼).
글꼴: 문단 첫 run 글자 모양의 한글 글꼴과 라틴 글꼴.
"""

import collections
import json
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
from pagediff import body_xml  # noqa: E402


def cell_paras(xmls):
    out = []
    for x in xmls:
        for m in re.finditer(r"<hp:tc\b[^>]*>\s*<hp:subList[^>]*>", x):
            depth, i, ps = 1, m.end(), []
            for t in re.finditer(r"<(/?)hp:subList\b[^>]*?(/?)>", x[i:]):
                if t.group(2):
                    continue
                depth += -1 if t.group(1) else 1
                if depth == 0:
                    seg = x[i : i + t.start()]
                    break
            ps, d, st = [], 0, None
            for t in re.finditer(r"<(/?)hp:(p|subList)\b[^>]*?(/?)>", seg):
                if t.group(2) == "subList":
                    if not t.group(3):
                        d += -1 if t.group(1) else 1
                    continue
                if d:
                    continue
                if not t.group(1) and not t.group(3):
                    st = t.start()
                elif t.group(1) and st is not None:
                    ps.append(seg[st : t.end()])
                    st = None
            out.append(ps)
    return out


def main(path):
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]
    cache = {}
    stat = collections.Counter()
    dirs = collections.Counter()
    for r in rows:
        doc = r["id"]
        if doc not in cache:
            z = zipfile.ZipFile(f"../out/oracle/{doc}.hwpx")
            names = sorted(n for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n))
            xmls = [z.read(n).decode() for n in names]
            h = z.read("Contents/header.xml").decode()
            faces = {}
            for lang in ("HANGUL", "LATIN"):
                b = re.search(rf'<hh:fontface lang="{lang}".*?</hh:fontface>', h, re.S).group(0)
                faces[lang] = dict(re.findall(r'<hh:font id="(\d+)" face="([^"]+)"', b))
            cache[doc] = (body_xml(f"../out/oracle/{doc}.hwpx"), cell_paras(xmls), h, faces)
        body, cells, h, faces = cache[doc]
        try:
            p = body[r["para"]] if r["where"] == "본문" else cells[r["cell"]][r["para"]]
        except IndexError:
            stat[("?", "?")] += 1
            continue
        cid = re.search(r'charPrIDRef="(\d+)"', re.sub(r"<hp:p\b[^>]*>", "", p, count=1))
        font = ("?", "?")
        if cid:
            cp = re.search(rf'<hh:charPr id="{cid.group(1)}".*?</hh:charPr>', h, re.S).group(0)
            fr = re.search(r'<hh:fontRef hangul="(\d+)" latin="(\d+)"', cp).groups()
            font = (faces["HANGUL"].get(fr[0], "?"), faces["LATIN"].get(fr[1], "?"))
        stat[font] += 1
        a, b = r["han"], r["rhwp"]
        d = next((i for i in range(min(len(a), len(b))) if a[i] != b[i]), None)
        if d is None:
            dirs["줄 수만 다름(" + ("rhwp 많음" if len(b) > len(a) else "rhwp 적음") + ")"] += 1
        else:
            dirs["rhwp 먼저 꺾음" if b[d] < a[d] else "rhwp 늦게 꺾음"] += 1
    print("방향", dirs.most_common())
    for (hf, lf), n in stat.most_common(25):
        print(f"  {n:4d}  한글 {hf} / 라틴 {lf}")


if __name__ == "__main__":
    main(sys.argv[1])
