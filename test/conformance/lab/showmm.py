"""불일치(nativescore --out) 한 줄을 한/글과 rhwp 줄 나눔으로 펼쳐 글로 보인다.

    python showmm.py <불일치.jsonl> <id> [본문|칸] [칸 순번] [문단]

줄 시작은 UTF-16 위치(조판 부호 포함)라 문단 XML 을 부호 자리까지 펼쳐 자른다. 조판 부호는 「¤」 로 보인다.
"""

import json
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
from mmstat import cell_paras  # noqa: E402
from pagediff import body_xml  # noqa: E402



def stream(p):
    """문단을 UTF-16 단위 글로 펼친다(조판 부호는 8칸, 탭과 줄바꿈 등은 1칸)."""
    p = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", p, flags=re.S)
    out = []
    for m in re.finditer(
        r"<hp:t>([^<]*)|<hp:t/>|<hp:(tab|lineBreak|fwSpace|nbSpace|hyphen)\b[^>]*/>|<hp:(fieldBegin|fieldEnd|bookmark|tbl|pic|rect|equation|compose|colPr|secPr|footNote|endNote|autoNum|newNum|pageNum|header|footer|indexmark)\b",
        p,
    ):
        if m.group(1) is not None:
            t = (
                m.group(1)
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&amp;", "&")
                .replace("&quot;", '"')
                .replace("&apos;", "'")
            )
            for ch in t:
                out.append(ch)
                if ord(ch) > 0xFFFF:
                    out.append("")
        elif m.group(2):
            out.append(
                {
                    "tab": "→",
                    "lineBreak": "↵",
                    "fwSpace": "␣",
                    "nbSpace": "·",
                    "hyphen": "-",
                }[m.group(2)]
            )
        elif m.group(3):
            out.extend(["¤"] + [""] * 7)
    return out


def main():
    path, doc = sys.argv[1], sys.argv[2]
    rows = [json.loads(line) for line in open(path, encoding="utf-8")]
    rows = [r for r in rows if r["id"] == doc]
    if len(sys.argv) > 3:
        where = sys.argv[3]
        rows = [r for r in rows if r["where"] == where]
        if where == "칸":
            rows = [
                r
                for r in rows
                if r.get("cell") == int(sys.argv[4]) and r["para"] == int(sys.argv[5])
            ]
        elif len(sys.argv) > 4:
            rows = [r for r in rows if r["para"] == int(sys.argv[4])]
    z = zipfile.ZipFile(f"../out/oracle/{doc}.hwpx")
    xmls = [
        z.read(n).decode()
        for n in sorted(
            x for x in z.namelist() if re.match(r"Contents/section\d+\.xml$", x)
        )
    ]
    body, cells = body_xml(f"../out/oracle/{doc}.hwpx"), cell_paras(xmls)
    for r in rows:
        p = body[r["para"]] if r["where"] == "본문" else cells[r["cell"]][r["para"]]
        s = stream(p)
        print(f"== {doc} {r['where']} {r.get('cell', '')} 문단 {r['para']}")
        for who in ("han", "rhwp"):
            st = r[who] + [len(s)]
            print(
                f"  {who:4s}", " | ".join("".join(s[a:b]) for a, b in zip(st, st[1:]))
            )


if __name__ == "__main__":
    main()
