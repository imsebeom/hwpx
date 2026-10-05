"""글자 폭 사다리: 시험 글마다 칸 글자 자리를 4 HWPUNIT 씩 바꾼 1×1 표를 한 문서에 넣고, 한글이 몇 줄로 나누는지 읽는다.

python wl.py make <spec.json> <out.hwpx>     spec: [{"text": "...", "char": 45, "est": 3936}, ...] (est = 예상 폭 HWPUNIT)
python wl.py read <spec.json> <한글 재저장.hwpx>  → 글마다 한 줄에 들어가는 가장 좁은 자리(= 한글 유효 폭)
바탕 문서는 g5.hwpx(9pt 함초롬바탕 charPr 45, 가운데 정렬 paraPr 38). 좌우 여백 283 고정, 칸 폭을 바꾼다.
"""

import json
import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).parent


def steps(item):
    span = item.get("span", 28)
    return list(range(-span, span + 4, 4))


def base_parts():
    src = zipfile.ZipFile(HERE / "g5.hwpx")
    members = [(it, src.read(it.filename)) for it in src.infolist()]
    sec = next(
        d for it, d in members if it.filename == "Contents/section0.xml"
    ).decode()
    h = sec.find("2. 창의적 체험활동 평가 계획")
    t = sec.find("<hp:tbl ", h)
    ps = sec.rfind("<hp:p ", 0, t)
    depth, end = 0, None
    for m in re.finditer(r"<hp:tbl\b|</hp:tbl>", sec[t:]):
        depth += 1 if m.group(0) == "<hp:tbl" else -1
        if depth == 0:
            end = t + m.end()
            break
    pe = sec.find("</hp:p>", end) + len("</hp:p>")
    return members, sec, sec[ps:t], sec[t:end], sec[end:pe], pe


def table_xml(tbl, text, char, avail):
    w = avail + 566
    head = tbl[: tbl.find("<hp:tr")]
    head = re.sub(r'rowCnt="\d+"', 'rowCnt="1"', head)
    head = re.sub(r'colCnt="\d+"', 'colCnt="1"', head)
    head = re.sub(r'(<hp:sz width=")\d+', rf"\g<1>{w}", head)
    head = re.sub(r'repeatHeader="1"', 'repeatHeader="0"', head)
    cell = (
        '<hp:tr><hp:tc name="" header="0" hasMargin="1" protect="0" editable="0" dirty="0" borderFillIDRef="13">'
        '<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">'
        f'<hp:p id="0" paraPrIDRef="38" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="{char}"><hp:t>{escape(text)}</hp:t></hp:run></hp:p>'
        '</hp:subList><hp:cellAddr colAddr="0" rowAddr="0"/><hp:cellSpan colSpan="1" rowSpan="1"/>'
        f'<hp:cellSz width="{w}" height="1300"/><hp:cellMargin left="283" right="283" top="170" bottom="170"/></hp:tc></hp:tr></hp:tbl>'
    )
    return head + cell


def make(spec_path, out):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    members, sec, p_open, tbl, p_close, pe = base_parts()
    paras = []
    for item in spec:
        base = item["est"] // 4 * 4
        for d in steps(item):
            paras.append(
                p_open + table_xml(tbl, item["text"], item["char"], base + d) + p_close
            )
    new_sec = sec[:pe] + "".join(paras) + sec[pe:]
    dst = zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED)
    for it, data in members:
        if it.filename == "Contents/section0.xml":
            data = new_sec.encode()
        elif (
            it.filename == "Contents/header.xml"
            and Path(spec_path).with_suffix(".charpr.json").exists()
        ):
            extra = json.loads(
                Path(spec_path).with_suffix(".charpr.json").read_text(encoding="utf-8")
            )
            hdr = data.decode()
            # {"fonts": [이름…], "variants": [{…, "face": 이름}]} 꼴이면 글꼴 목록부터 늘린다
            if isinstance(extra, dict):
                hdr, ids = add_fonts(hdr, extra["fonts"])
                for v in extra["variants"]:
                    v["fontref"] = ids[v["face"]]
                extra = extra["variants"]
            data = add_charprs(hdr, extra).encode()
        dst.writestr(
            it,
            data,
            compress_type=zipfile.ZIP_STORED
            if it.filename == "mimetype"
            else zipfile.ZIP_DEFLATED,
        )
    dst.close()
    print("tables", len(paras))


def add_fonts(hdr, faces):
    """글꼴 이름들을 언어별 글꼴 목록 끝에 덧붙인다. 반환: (hdr, {이름: {LANG: id}})."""
    ids = {f: {} for f in faces}

    def one(m):
        lang, cnt, body = m.group(1), int(m.group(2)), m.group(3)
        add = ""
        for i, f in enumerate(faces):
            ids[f][lang] = cnt + i
            add += (
                f'<hh:font id="{cnt + i}" face="{f}" type="TTF" isEmbedded="0">'
                '<hh:typeInfo familyType="FCAT_GOTHIC" weight="6" proportion="0" contrast="0" '
                'strokeVariation="1" armStyle="1" letterform="1" midline="1" xHeight="1"/></hh:font>'
            )
        return f'<hh:fontface lang="{lang}" fontCnt="{cnt + len(faces)}">{body}{add}</hh:fontface>'

    hdr = re.sub(
        r'<hh:fontface lang="(\w+)" fontCnt="(\d+)">(.*?)</hh:fontface>',
        one,
        hdr,
        flags=re.S,
    )
    return hdr, ids


def add_charprs(hdr, extra):
    """extra: [{"id": 100, "height": 1000, "font": 4}] — charPr 45 를 본떠 크기와 글꼴만 바꾼 것을 덧붙인다."""
    m = re.search(r'<hh:charPr id="45".*?</hh:charPr>', hdr, re.S).group(0)
    add = ""
    for e in extra:
        c = m.replace('id="45"', f'id="{e["id"]}"', 1)
        c = re.sub(r'height="\d+"', f'height="{e["height"]}"', c, count=1)
        langs = ("hangul", "latin", "hanja", "japanese", "other", "symbol", "user")
        ref = e.get("fontref") or {k.upper(): e["font"] for k in langs}
        c = re.sub(
            r"<hh:fontRef [^>]*/>",
            "<hh:fontRef " + " ".join(f'{k}="{ref[k.upper()]}"' for k in langs) + "/>",
            c,
            count=1,
        )
        if "spacing" in e:
            c = re.sub(
                r"<hh:spacing [^>]*/>",
                "<hh:spacing "
                + " ".join(
                    f'{k}="{e["spacing"]}"'
                    for k in (
                        "hangul",
                        "latin",
                        "hanja",
                        "japanese",
                        "other",
                        "symbol",
                        "user",
                    )
                )
                + "/>",
                c,
                count=1,
            )
        if "ratio" in e:
            c = re.sub(
                r"<hh:ratio [^>]*/>",
                "<hh:ratio "
                + " ".join(
                    f'{k}="{e["ratio"]}"'
                    for k in (
                        "hangul",
                        "latin",
                        "hanja",
                        "japanese",
                        "other",
                        "symbol",
                        "user",
                    )
                )
                + "/>",
                c,
                count=1,
            )
        if e.get("bold") is False:
            c = c.replace("<hh:bold/>", "")
        add += c
    n = int(re.search(r'<hh:charProperties itemCnt="(\d+)"', hdr).group(1))
    ids = [int(x) for x in re.findall(r'<hh:charPr id="(\d+)"', hdr)]
    assert max(ids) == n - 1, (max(ids), n)
    # id 는 이어져야 하므로 e["id"] 는 n 부터 차례로 준다
    assert [e["id"] for e in extra] == list(range(n, n + len(extra))), (
        n,
        [e["id"] for e in extra],
    )
    hdr = hdr.replace(
        f'<hh:charProperties itemCnt="{n}"',
        f'<hh:charProperties itemCnt="{n + len(extra)}"',
    )
    return hdr.replace("</hh:charProperties>", add + "</hh:charProperties>")


def read(spec_path, resaved):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    sec = zipfile.ZipFile(resaved).read("Contents/section0.xml").decode()
    h = sec.find("2. 창의적 체험활동 평가 계획")
    tables = [m.start() for m in re.finditer(r"<hp:tbl ", sec[h:])]
    tables = [h + t for t in tables][1:]  # 첫 표는 원래 표
    assert len(tables) >= sum(len(steps(i)) for i in spec), (
        len(tables),
        sum(len(steps(i)) for i in spec),
    )
    at = 0
    out = []
    for i, item in enumerate(spec):
        base = item["est"] // 4 * 4
        fit = None
        lines_at = []
        for j, d in enumerate(steps(item)):
            t = tables[at + j]
            cell = sec[t : sec.find("</hp:tbl>", t)]
            n = len(re.findall(r"<hp:lineseg ", cell))
            lines_at.append(n)
            if n == 1 and fit is None:
                fit = base + d
        mono = all(a >= b for a, b in zip(lines_at, lines_at[1:]))
        at += len(steps(item))
        out.append({**item, "fit": fit, "mono": mono, "lines": lines_at})
        print(
            f"{item['text']!r:<28} char {item['char']:<4} 예상 {item['est']:<6} 한글 {fit}  차 {None if fit is None else fit - item['est']}  {'' if mono else '비단조 ' + str(lines_at)}"
        )
    Path(spec_path).with_suffix(".result.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"
    )


if sys.argv[1] == "make":
    make(sys.argv[2], sys.argv[3])
else:
    read(sys.argv[2], sys.argv[3])
