"""불일치(nativescore --out)를 문단 머리 종류(번호, 글머리표, 개요, 없음)와 어긋난 줄로 묶는다.

    python headstat.py <불일치.jsonl> [--list NUMBER]

어긋난 줄: 첫 줄(0)에서 갈리면 머리 폭이 의심이고, 이어지는 줄이면 내어쓰기나 본문 폭 쪽이다.
"""

import collections
import json
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
from mmstat import cell_paras  # noqa: E402
from pagediff import body_xml  # noqa: E402


def load(doc, cache):
    if doc not in cache:
        path = f"../out/oracle/{doc}.hwpx"
        z = zipfile.ZipFile(path)
        names = sorted(
            n for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n)
        )
        xmls = [z.read(n).decode() for n in names]
        h = z.read("Contents/header.xml").decode()
        cache[doc] = (body_xml(path), cell_paras(xmls), h)
    return cache[doc]


def head_of(p, h):
    pid = re.search(r'paraPrIDRef="(\d+)"', p).group(1)
    pp = re.search(rf'<hh:paraPr id="{pid}"[\s\S]*?</hh:paraPr>', h).group(0)
    m = re.search(r'<hh:heading type="(\w+)" idRef="(\d+)" level="(\d+)"', pp)
    return (m.group(1), m.group(2), m.group(3)) if m else ("NONE", "0", "0")


def main(path, want=None):
    rows = [json.loads(line) for line in open(path, encoding="utf-8")]
    cache = {}
    stat = collections.Counter()
    for r in rows:
        body, cells, h = load(r["id"], cache)
        try:
            p = body[r["para"]] if r["where"] == "본문" else cells[r["cell"]][r["para"]]
        except (IndexError, KeyError):
            stat[("?", "?")] += 1
            continue
        kind, ref, level = head_of(p, h)
        a, b = r["han"], r["rhwp"]
        d = next((i for i in range(min(len(a), len(b))) if a[i] != b[i]), None)
        line = "줄 수" if d is None else ("첫 줄" if d == 1 else "이후 줄")
        side = "" if d is None else ("rhwp 먼저" if b[d] < a[d] else "rhwp 늦게")
        stat[(kind, line + " " + side)] += 1
        if want and kind == want:
            print(
                r["id"],
                r["where"],
                r.get("cell", ""),
                r["para"],
                f"ref={ref} lv={level}",
                line,
                side,
                a[:3],
                b[:3],
                r.get("text", "")[:50],
            )
    for (kind, line), n in sorted(stat.items(), key=lambda kv: (kv[0][0], -kv[1])):
        print(f"{n:4d}  {kind:8s} {line}")


if __name__ == "__main__":
    want = sys.argv[sys.argv.index("--list") + 1] if "--list" in sys.argv else None
    main(sys.argv[1], want)
