"""불일치마다 처음 갈라지는 줄의 꺾는 자리 앞뒤 글자를 한/글과 rhwp 로 나란히 보인다.

    python mmctx.py <불일치.jsonl> [글꼴 일부] [먼저|늦게] [최대 개수]

글꼴은 문단 첫 run 의 한글 글꼴 이름 일부로 거른다(mmstat 와 같은 기준). 먼저 = rhwp 가 먼저 꺾음(넓게 잼).
한 줄: 문서 위치, 갈라진 줄 번호, 한/글 줄 끝 10자 | 다음 줄 첫 3자, rhwp 같은 것, 차이(UTF-16 칸).
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
    path = sys.argv[1]
    want_font = sys.argv[2] if len(sys.argv) > 2 else ""
    want_dir = sys.argv[3] if len(sys.argv) > 3 else ""
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else 40
    cache = {}
    shown = 0
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        doc = r["id"]
        if doc not in cache:
            z = zipfile.ZipFile(f"../out/oracle/{doc}.hwpx")
            names = sorted(
                n for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n)
            )
            xmls = [z.read(n).decode() for n in names]
            h = z.read("Contents/header.xml").decode()
            faces = {}
            for lang in ("HANGUL", "LATIN"):
                b = re.search(
                    rf'<hh:fontface lang="{lang}".*?</hh:fontface>', h, re.S
                ).group(0)
                faces[lang] = dict(re.findall(r'<hh:font id="(\d+)" face="([^"]+)"', b))
            cache[doc] = (
                body_xml(f"../out/oracle/{doc}.hwpx"),
                cell_paras(xmls),
                h,
                faces,
            )
        body, cells, h, faces = cache[doc]
        try:
            p = body[r["para"]] if r["where"] == "본문" else cells[r["cell"]][r["para"]]
        except IndexError:
            continue
        cid = re.search(
            r'charPrIDRef="(\d+)"', re.sub(r"<hp:p\b[^>]*>", "", p, count=1)
        )
        font = "?"
        size = "?"
        if cid:
            cp = re.search(
                rf'<hh:charPr id="{cid.group(1)}".*?</hh:charPr>', h, re.S
            ).group(0)
            font = faces["HANGUL"].get(
                re.search(r'<hh:fontRef hangul="(\d+)"', cp).group(1), "?"
            )
            size = re.search(r'height="(\d+)"', cp).group(1)
        if want_font and want_font not in font:
            continue
        a, b = r["han"], r["rhwp"]
        d = next((i for i in range(min(len(a), len(b))) if a[i] != b[i]), None)
        if d is None:
            continue
        early = b[d] < a[d]
        if want_dir == "먼저" and not early or want_dir == "늦게" and early:
            continue
        s = stream(p)

        def ctx(at):
            return f"{s[max(0, at - 10) : at]!s:>10}|{s[at : at + 3]}"

        where = f"{doc} {r['where']} {'c' + str(r['cell']) + ' ' if r['where'] == '칸' else ''}p{r['para']}"
        print(
            f"{where:<22} {font}/{size} 줄{d}  한/글 {ctx(a[d])}  rhwp {ctx(b[d])}  차 {b[d] - a[d]}"
        )
        shown += 1
        if shown >= limit:
            break


if __name__ == "__main__":
    main()
