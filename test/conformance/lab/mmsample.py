"""불일치 줄의 첫 차이 자리 앞뒤 글을 한/글과 rhwp 로 나란히 찍는다(조판 부호 없는 문단만).

    python mmsample.py <불일치.jsonl> [개수=30] [씨앗=1]
"""

import html
import json
import random
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
from mmstat import cell_paras  # noqa: E402
from pagediff import body_xml  # noqa: E402


def main(path, n=30, seed=1):
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]
    random.Random(seed).shuffle(rows)
    shown = 0
    for r in rows:
        d = r["id"]
        z = zipfile.ZipFile(f"../out/oracle/{d}.hwpx")
        xs = [z.read(x).decode() for x in sorted(x for x in z.namelist() if re.match(r"Contents/section\d+\.xml$", x))]
        try:
            p = body_xml(f"../out/oracle/{d}.hwpx")[r["para"]] if r["where"] == "본문" else cell_paras(xs)[r["cell"]][r["para"]]
        except IndexError:
            continue
        body = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", p)
        if re.search(r"<hp:(ctrl|tbl|pic|tab|lineBreak|fwSpace|nbSpace|hyphen|equation|rect|line|container|secPr|colPr)\b", body):
            continue
        t = html.unescape("".join(re.findall(r"<hp:t>([^<]*)</hp:t>", body)))
        a, b = r["han"], r["rhwp"]
        i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
        ha = a[i] if i < len(a) else len(t)
        rb = b[i] if i < len(b) else len(t)
        lo = min(ha, rb)
        print(f"{d} {r['where']} {r.get('cell')}:{r['para']} 한글 {ha} rhwp {rb} | {t[max(0, lo - 12):lo]!r} ‖ {t[lo:max(ha, rb) + 3]!r}")
        shown += 1
        if shown >= n:
            break


if __name__ == "__main__":
    main(sys.argv[1], *(int(x) for x in sys.argv[2:]))
