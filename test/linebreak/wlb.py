"""글머리표 자리 사다리. co2.hwpx(글머리표 문단 paraPr 25, 글머리표 정의 둘)를 바탕으로 1×1 표를 줄줄이 넣는다.

python wlb.py make <spec.json> <out.hwpx>
python wlb.py read <spec.json> <한글 재저장.hwpx>
spec: {"bullets": [{"char": "•", "offset": 50, "auto": 1, "adjust": 0}, ...],     # id 3 부터 덧붙는다
       "items": [{"text": "...", "bullet": 1, "char": 0, "est": 12000, "span": 720, "step": 16}, ...]}
"""

import json
import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).parent
ANCHOR = "평가 요소"


def steps(item):
    return list(range(-item["span"], item["span"] + item["step"], item["step"]))


def parts():
    src = zipfile.ZipFile(HERE / "co2.hwpx")
    members = [(it, src.read(it.filename)) for it in src.infolist()]
    sec = next(
        d for it, d in members if it.filename == "Contents/section0.xml"
    ).decode()
    hdr = next(d for it, d in members if it.filename == "Contents/header.xml").decode()
    t = sec.rfind(
        "<hp:tbl ", 0, sec.find("III. 채점 기준")
    )  # 본문 표 아무거나의 머리를 틀로 쓴다
    t = sec.find("<hp:tbl ")
    ps = sec.rfind("<hp:p ", 0, t)
    depth, end = 0, None
    for m in re.finditer(r"<hp:tbl\b|</hp:tbl>", sec[t:]):
        depth += 1 if m.group(0) == "<hp:tbl" else -1
        if depth == 0:
            end = t + m.end()
            break
    pe = sec.find("</hp:p>", end) + len("</hp:p>")
    return members, sec, hdr, sec[ps:t], sec[t:end], sec[end:pe], pe


def table_xml(tbl, text, para, char, avail):
    w = avail + 1020
    head = tbl[: tbl.find("<hp:tr")]
    head = re.sub(r'rowCnt="\d+"', 'rowCnt="1"', head)
    head = re.sub(r'colCnt="\d+"', 'colCnt="1"', head)
    head = re.sub(r'(<hp:sz width=")\d+', rf"\g<1>{w}", head)
    head = re.sub(r'(<hp:sz [^>]*height=")\d+', r"\g<1>1500", head)
    head = head.replace('pageBreak="CELL"', 'pageBreak="NONE"').replace(
        'repeatHeader="1"', 'repeatHeader="0"'
    )
    cell = (
        '<hp:tr><hp:tc name="" header="0" hasMargin="1" protect="0" editable="0" dirty="0" borderFillIDRef="3">'
        '<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">'
        f'<hp:p id="0" paraPrIDRef="{para}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="{char}"><hp:t>{escape(text)}</hp:t></hp:run></hp:p>'
        '</hp:subList><hp:cellAddr colAddr="0" rowAddr="0"/><hp:cellSpan colSpan="1" rowSpan="1"/>'
        f'<hp:cellSz width="{w}" height="1500"/><hp:cellMargin left="510" right="510" top="141" bottom="141"/></hp:tc></hp:tr></hp:tbl>'
    )
    return head + cell


def patch_header(hdr, bullets):
    """글머리표 정의를 덧붙이고, 정의마다 paraPr 25 를 본뜬 문단 모양을 만든다. 반환: (hdr, {bullet id: paraPr id})."""
    n_b = int(re.search(r'<hh:bullets itemCnt="(\d+)"', hdr).group(1))
    n_p = int(re.search(r'<hh:paraProperties itemCnt="(\d+)"', hdr).group(1))
    base = next(m.group(0) for m in re.finditer(r'<hh:paraPr id="\d+".*?</hh:paraPr>', hdr, re.S) if 'type="BULLET" idRef="1"' in m.group(0))
    base_id = re.match(r'<hh:paraPr id="(\d+)"', base).group(1)
    add_b, add_p, para_of = "", "", {1: int(base_id)}
    ids = list(range(2, n_b + 1)) + [n_b + 1 + i for i in range(len(bullets))]
    for i, b in enumerate(bullets):
        bid = n_b + 1 + i
        add_b += (
            f'<hh:bullet id="{bid}" char={quoteattr(b["char"])} useImage="0"><hh:paraHead level="0" align="LEFT" useInstWidth="0" '
            f'autoIndent="{b.get("auto", 1)}" widthAdjust="{b.get("adjust", 0)}" textOffsetType="PERCENT" textOffset="{b["offset"]}" '
            'numFormat="DIGIT" charPrIDRef="4294967295" checkable="0"/></hh:bullet>'
        )
    for k, bid in enumerate(ids):
        pid = n_p + k
        add_p += base.replace(f'id="{base_id}"', f'id="{pid}"', 1).replace(
            'type="BULLET" idRef="1"', f'type="BULLET" idRef="{bid}"'
        )
        para_of[bid] = pid
    hdr = hdr.replace(
        f'<hh:bullets itemCnt="{n_b}"', f'<hh:bullets itemCnt="{n_b + len(bullets)}"'
    ).replace("</hh:bullets>", add_b + "</hh:bullets>")
    hdr = hdr.replace(
        f'<hh:paraProperties itemCnt="{n_p}"',
        f'<hh:paraProperties itemCnt="{n_p + len(ids)}"',
    ).replace("</hh:paraProperties>", add_p + "</hh:paraProperties>")
    return hdr, para_of


def make(spec_path, out):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    members, sec, hdr, p_open, tbl, p_close, pe = parts()
    hdr, para_of = patch_header(hdr, spec["bullets"])
    paras = []
    for item in spec["items"]:
        base = item["est"] // 4 * 4
        for d in steps(item):
            paras.append(
                p_open
                + table_xml(
                    tbl, item["text"], para_of[item["bullet"]], item["char"], base + d
                )
                + p_close
            )
    new_sec = sec[:pe] + "".join(paras) + sec[pe:]
    dst = zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED)
    for it, data in members:
        if it.filename == "Contents/section0.xml":
            data = new_sec.encode()
        elif it.filename == "Contents/header.xml":
            data = hdr.encode()
        dst.writestr(
            it,
            data,
            compress_type=zipfile.ZIP_STORED
            if it.filename == "mimetype"
            else zipfile.ZIP_DEFLATED,
        )
    dst.close()
    print("tables", len(paras), "paraPr", para_of)


def read(spec_path, resaved):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    sec = zipfile.ZipFile(resaved).read("Contents/section0.xml").decode()
    first = sec.find("<hp:tbl ")
    depth, end = 0, None
    for m in re.finditer(r"<hp:tbl\b|</hp:tbl>", sec[first:]):
        depth += 1 if m.group(0) == "<hp:tbl" else -1
        if depth == 0:
            end = first + m.end()
            break
    tables = [end + m.start() for m in re.finditer(r"<hp:tbl ", sec[end:])]
    at, out = 0, []
    for item in spec["items"]:
        base = item["est"] // 4 * 4
        counts = []
        for j, d in enumerate(steps(item)):
            t = tables[at + j]
            cell = sec[t : sec.find("</hp:tbl>", t)]
            counts.append((base + d, len(re.findall(r"<hp:lineseg ", cell))))
        at += len(steps(item))
        trans = [
            (b, n0, n1) for (a, n0), (b, n1) in zip(counts, counts[1:]) if n0 != n1
        ]
        out.append(
            {**item, "trans": trans, "first": counts[0][1], "last": counts[-1][1]}
        )
        print(
            f"bullet {item['bullet']} char {item['char']} {item['text']!r:<26} 줄 수 {counts[0][1]}→{counts[-1][1]}  바뀌는 자리(이상이면 줄어듦) {trans}"
        )
    Path(spec_path).with_suffix(".result.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"
    )


{"make": make, "read": read}[sys.argv[1]](sys.argv[2], sys.argv[3])
