"""줄 끝이 빈칸 줄 가운데서 갈라지는 불일치를 모아, 빈칸 줄 길이와 한/글, rhwp 가 줄 끝에 남긴 빈칸 수를 센다.

python mmspace.py <불일치.jsonl>
"""

import json
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
from mmstat import cell_paras  # noqa: E402
from pagediff import body_xml  # noqa: E402
from showmm import stream  # noqa: E402


def main():
    cache = {}
    for line in open(sys.argv[1], encoding="utf-8"):
        r = json.loads(line)
        doc = r["id"]
        if doc not in cache:
            z = zipfile.ZipFile(f"../out/oracle/{doc}.hwpx")
            xmls = [
                z.read(n).decode()
                for n in sorted(
                    x for x in z.namelist() if re.match(r"Contents/section\d+\.xml$", x)
                )
            ]
            cache[doc] = (body_xml(f"../out/oracle/{doc}.hwpx"), cell_paras(xmls))
        body, cells = cache[doc]
        try:
            p = body[r["para"]] if r["where"] == "본문" else cells[r["cell"]][r["para"]]
        except IndexError:
            continue
        a, b = r["han"], r["rhwp"]
        d = next((i for i in range(min(len(a), len(b))) if a[i] != b[i]), None)
        if d is None:
            continue
        s = stream(p)
        cut = min(a[d], b[d])
        # 갈라진 자리 앞뒤가 빈칸 줄인가
        if not (
            0 < cut <= len(s)
            and s[cut - 1] == " "
            and max(a[d], b[d]) <= len(s)
            and s[max(a[d], b[d]) - 1] == " "
        ):
            continue
        i = cut
        while i > 0 and s[i - 1] == " ":
            i -= 1
        j = cut
        while j < len(s) and s[j] == " ":
            j += 1
        run = j - i
        han_tail = a[d] - i
        rhwp_tail = b[d] - i
        start = a[d - 1] if d > 0 else 0
        where = f"{doc} {r['where']} {'c' + str(r['cell']) + ' ' if r['where'] == '칸' else ''}p{r['para']}"
        print(
            f"{where:<22} 빈칸 줄 {run:2d}  한/글 줄끝 {han_tail}  rhwp {rhwp_tail}  앞글 「{''.join(s[max(start, i - 6) : i])}」"
        )


if __name__ == "__main__":
    main()
