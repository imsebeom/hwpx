"""불일치 줄에서 한/글이 실제로 담은 줄을 등록 폭 표(out/metrics/<id>.json)와 한/글 폭 규칙으로 재어 줄 폭과 견준다.

    python linecheck.py <불일치.jsonl> [개수=40]

글자 폭 = 4 HWPUNIT 단위로 반올림한 (표 폭 × 크기 × 장평) + 자간(그 폭의 %, 반올림). 빈칸은 「글꼴에 어울리는 빈칸」 꺼짐이면
크기의 절반. 줄 끝 빈칸은 세지 않는다. 계산 폭이 줄 폭(horzsize)을 넘으면 우리 폭이 넓은 것이고, 그런 줄에 든 글자를 센다.
본문, 칸 문단 가운데 조판 부호(탭, 개체 등)가 없는 것만 본다.
"""

import collections
import html
import json
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
from mmstat import cell_paras  # noqa: E402
from pagediff import body_xml  # noqa: E402

LANG = {
    "HANGUL": 0,
    "LATIN": 1,
    "HANJA": 2,
    "JAPANESE": 3,
    "OTHER": 4,
    "SYMBOL": 5,
    "USER": 6,
}
LATIN_PUNCT = (
    set(" !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")
    | set(chr(c) for c in range(0xA0, 0x100))
    | set("‘’“”")
)
SYMBOL_SET = set("–—―†‡•…‰′″※‼™℃")


def lang_of(ch):
    o = ord(ch)
    if ch in SYMBOL_SET:
        return "SYMBOL"
    if o < 0x80 or ch in LATIN_PUNCT or 0x100 <= o < 0x250:
        return "LATIN"
    if 0xAC00 <= o <= 0xD7A3 or 0x3130 <= o <= 0x318F or 0x1100 <= o <= 0x11FF:
        return "HANGUL"
    if 0x4E00 <= o <= 0x9FFF:
        return "HANJA"
    return "SYMBOL"


def widths_table(metrics):
    out = {}
    for m in metrics:
        if m.get("bold"):
            continue
        w = {}
        for start, arr in m.get("ranges", []):
            for i, v in enumerate(arr):
                if v:
                    w[chr(start + i)] = v
        out[m["name"]] = (
            m.get("em") or 1000,
            m.get("hangul"),
            w,
            m.get("uniform") or [],
        )
    return out


def char_units(ch, face, size, ratio, spacing, ufs, tables):
    em, hangul, w, uniform = tables.get(face, (1000, None, {}, []))
    if ch == " " and not ufs:
        base = size / 2
        u = (base // 4) if ratio == 100 else round(base / 4 * ratio / 100)
    else:
        if "가" <= ch <= "힣":
            gw = (
                hangul
                if isinstance(hangul, int)
                else (hangul[ord(ch) - 0xAC00] if isinstance(hangul, list) else None)
            )
        else:
            gw = w.get(ch)
            if gw is None:
                for a, b, v in uniform:
                    if a <= ord(ch) <= b:
                        gw = v
        if gw is None:
            return None
        base = gw * size / em
        u = round(base / 4) if ratio == 100 else int(base / 4 * ratio / 100)
    return u + round(u * spacing / 100)


def main(path, n=40):
    rows = [json.loads(line) for line in open(path, encoding="utf-8")]
    cache = {}
    over = collections.Counter()
    shown = 0
    stat = collections.Counter()
    for r in rows:
        d = r["id"]
        if d not in cache:
            z = zipfile.ZipFile(f"../out/oracle/{d}.hwpx")
            xs = [
                z.read(x).decode()
                for x in sorted(
                    x for x in z.namelist() if re.match(r"Contents/section\d+\.xml$", x)
                )
            ]
            h = z.read("Contents/header.xml").decode()
            faces = {}
            for lang in LANG:
                b = re.search(
                    rf'<hh:fontface lang="{lang}".*?</hh:fontface>', h, re.S
                ).group(0)
                faces[lang] = dict(re.findall(r'<hh:font id="(\d+)" face="([^"]+)"', b))
            metrics = json.load(open(f"../out/metrics/{d}.json", encoding="utf-8"))
            cache[d] = (
                body_xml(f"../out/oracle/{d}.hwpx"),
                cell_paras(xs),
                h,
                faces,
                widths_table(metrics),
            )
        body, cells, h, faces, tables = cache[d]
        try:
            p = body[r["para"]] if r["where"] == "본문" else cells[r["cell"]][r["para"]]
        except IndexError:
            continue
        clean = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", p)
        if re.search(
            r"<hp:(ctrl|tbl|pic|tab|lineBreak|fwSpace|nbSpace|hyphen|equation|rect|line|container|secPr|colPr)\b",
            clean,
        ):
            continue
        segs = re.findall(r'<hp:lineseg textpos="(\d+)"[^>]*horzsize="(\d+)"', p)
        a, b = r["han"], r["rhwp"]
        k = next((i for i in range(min(len(a), len(b))) if a[i] != b[i]), None)
        if k is None or k == 0:
            continue
        lo, hi = a[k - 1], a[k]
        horz = int(segs[k - 1][1])
        chars = []
        for cid, t in re.findall(
            r'<hp:run charPrIDRef="(\d+)">(.*?)</hp:run>', clean, re.S
        ):
            cp = re.search(rf'<hh:charPr id="{cid}".*?</hh:charPr>', h, re.S).group(0)
            size = int(re.search(r'height="(\d+)"', cp).group(1))
            ufs = re.search(r'useFontSpace="1"', cp) is not None
            fr = dict(
                re.findall(
                    r'(\w+)="(\d+)"', re.search(r"<hh:fontRef [^>]*/>", cp).group(0)
                )
            )
            ra = dict(
                re.findall(
                    r'(\w+)="(-?\d+)"', re.search(r"<hh:ratio [^>]*/>", cp).group(0)
                )
            )
            sp = dict(
                re.findall(
                    r'(\w+)="(-?\d+)"', re.search(r"<hh:spacing [^>]*/>", cp).group(0)
                )
            )
            for ch in html.unescape(re.sub(r"<[^>]+>", "", t)):
                lang = lang_of(ch)
                key = lang.lower()
                chars.append(
                    (
                        ch,
                        faces[lang].get(fr[key]),
                        size,
                        int(ra[key]),
                        int(sp[key]),
                        ufs,
                    )
                )
        line = chars[lo:hi]
        while line and line[-1][0] == " ":
            line = line[:-1]
        tot, unknown = 0, False
        for ch, face, size, ratio, spc, ufs in line:
            u = char_units(ch, face, size, ratio, spc, ufs, tables)
            if u is None:
                unknown = True
                break
            tot += u * 4
        if unknown:
            stat["모르는 글자"] += 1
            continue
        kind = "rhwp 먼저" if b[k] < a[k] else "rhwp 늦게"
        if tot > horz:
            stat[f"{kind}: 계산 폭 > 줄 폭(우리 폭 넓음)"] += 1
            for ch in set(c[0] for c in line):
                over[ch] += 1
        else:
            stat[f"{kind}: 계산 폭 ≤ 줄 폭"] += 1
        if shown < n and tot > horz:
            print(
                d,
                r["where"],
                r.get("cell"),
                r["para"],
                f"폭 {tot} > {horz}",
                "".join(c[0] for c in line)[-30:],
            )
            shown += 1
    print(stat.most_common())
    print(
        "넓게 잰 줄의 글자:",
        [(c, v) for c, v in over.most_common(40) if not ("가" <= c <= "힣")],
    )


if __name__ == "__main__":
    main(sys.argv[1], *(int(x) for x in sys.argv[2:]))
