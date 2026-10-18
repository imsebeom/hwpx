"""정답본에서 본문 문단에 앵커된 글자처럼 취급하지 않는 어울림(SQUARE) 개체를 세고, 단 폭 대비 남는 폭을 본다."""

import glob
import re
import sys
import zipfile
from pathlib import Path

from lxml import etree

sys.stdout.reconfigure(encoding="utf-8")
HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
OBJ = {
    "pic",
    "ole",
    "rect",
    "ellipse",
    "line",
    "polygon",
    "curve",
    "arc",
    "container",
    "connectLine",
    "textart",
    "equation",
}
root_dir = Path(sys.argv[1])
rows = []
for f in sorted(glob.glob(str(root_dir / "*.hwpx"))):
    z = zipfile.ZipFile(f)
    for name in sorted(
        n for n in z.namelist() if re.match(r"Contents/section\d+\.xml", n)
    ):
        s = z.read(name)
        if b'textWrap="SQUARE"' not in s:
            continue
        root = etree.fromstring(s)
        pg = re.search(rb'<hp:pagePr[^>]*width="(\d+)"', s)
        mg = re.search(rb'<hp:margin[^>]*left="(\d+)"[^>]*right="(\d+)"', s)
        col = int(pg.group(1)) - int(mg.group(1)) - int(mg.group(2)) if pg and mg else 0
        for p in root.iter(f"{HP}p"):
            if any(a.tag == f"{HP}tc" for a in p.iterancestors()):
                continue
            objs = []
            for el in p.iter():
                ln = etree.QName(el).localname
                if ln not in OBJ or el.get("textWrap") != "SQUARE":
                    continue
                pos = el.find(f"{HP}pos")
                sz = el.find(f"{HP}sz")
                if (
                    pos is None
                    or sz is None
                    or pos.get("treatAsChar") == "1"
                    or pos.get("vertRelTo") != "PARA"
                ):
                    continue
                if any(etree.QName(a).localname in OBJ for a in el.iterancestors()):
                    continue
                x = int(pos.get("horzOffset") or 0)
                objs.append(
                    (
                        x,
                        x + int(sz.get("width") or 0),
                        pos.get("horzRelTo"),
                        pos.get("horzAlign"),
                        ln,
                    )
                )
            if objs:
                cover = sum(b - a for a, b, *_ in objs)
                rows.append(
                    (Path(f).stem, name[-12:], p.get("id"), len(objs), col, cover, objs)
                )
for r in rows:
    print(
        r[0],
        r[1],
        "문단",
        r[2],
        "개체",
        r[3],
        "단",
        r[4],
        "덮는 폭",
        r[5],
        "남음",
        r[4] - r[5],
        [(o[4], o[2], o[3], o[0], o[1]) for o in r[6]][:3],
    )
print("합계", len(rows))
