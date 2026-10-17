"""조판 실험 문서 만들기: base.hwpx 의 글꼴, 글자 모양, 문단 모양을 바꾼 변형을 만든다.

    python make.py <변형.json> <출력 폴더>

변형.json 은 [{"name", "face", "height", "ratio", "spacing", "useFontSpace", "align", "condense", "paras": [글, ...]}, ...]
빠진 값은 base 그대로(글꼴 Pretendard, 10pt, 100%, 0, 0, JUSTIFY, condense 0). 들여쓰기는 0 으로 둔다.
"""

import json
import os
import re
import sys
import zipfile
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
LANGS = ("hangul", "latin", "hanja", "japanese", "other", "symbol", "user")


def lang_attrs(tag, value):
    return f"<hh:{tag} " + " ".join(f'{k}="{value}"' for k in LANGS) + "/>"


def make(v, out_dir):
    src = zipfile.ZipFile(os.path.join(HERE, "base.hwpx"))
    header = src.read("Contents/header.xml").decode("utf-8")
    section = src.read("Contents/section0.xml").decode("utf-8")

    # langFaces: {"HANGUL": "휴먼명조", "LATIN": "맑은 고딕", ...} — 언어 범주마다 글자 모양 0 이 쓰는 글꼴(id 1)을 바꾼다
    for lang, face in (v.get("langFaces") or {}).items():
        block = re.search(
            rf'<hh:fontface lang="{lang}"[\s\S]*?</hh:fontface>', header
        ).group(0)
        new_block = re.sub(
            r'(<hh:font id="1" face=")[^"]*"', rf'\g<1>{escape(face)}"', block
        )
        if v.get(
            "fontType"
        ):  # "HFT" 면 한컴 내장 글꼴로 찾는다(TTF 로 두면 한/글이 다른 글꼴로 바꿔 쓴다)
            new_block = re.sub(
                r'(<hh:font id="1" face="[^"]*" type=")\w+"',
                rf'\g<1>{v["fontType"]}"',
                new_block,
            )
        header = header.replace(block, new_block)
    if "face" in v:
        header = header.replace('face="Pretendard"', f'face="{escape(v["face"])}"')
    cp = re.search(r'<hh:charPr id="0"[\s\S]*?</hh:charPr>', header).group(0)
    new = cp
    if "height" in v:
        new = re.sub(r'height="\d+"', f'height="{v["height"]}"', new, count=1)
    if v.get("bold") and "<hh:bold/>" not in new:
        new = new.replace("<hh:underline ", "<hh:bold/><hh:underline ", 1)
    if "useFontSpace" in v:
        new = re.sub(r'useFontSpace="\d"', f'useFontSpace="{v["useFontSpace"]}"', new)
    if "ratio" in v:
        new = re.sub(r"<hh:ratio [^>]*/>", lang_attrs("ratio", v["ratio"]), new)
    if "spacing" in v:
        new = re.sub(r"<hh:spacing [^>]*/>", lang_attrs("spacing", v["spacing"]), new)
    header = header.replace(cp, new)

    pp = re.search(r'<hh:paraPr id="0"[\s\S]*?</hh:paraPr>', header).group(0)
    newp = re.sub(
        r'<hc:intent value="-?\d+"', f'<hc:intent value="{v.get("intent", 0)}"', pp
    )
    if "left" in v:
        newp = re.sub(r'<hc:left value="-?\d+"', f'<hc:left value="{v["left"]}"', newp)
    if "align" in v:
        newp = re.sub(
            r'<hh:align horizontal="\w+"', f'<hh:align horizontal="{v["align"]}"', newp
        )
    if "condense" in v:
        newp = re.sub(r'condense="\d+"', f'condense="{v["condense"]}"', newp)
    for key in ("breakLatinWord", "breakNonLatinWord"):
        if key in v:
            newp = re.sub(rf'{key}="\w+"', f'{key}="{v[key]}"', newp)
    if "right" in v:  # 오른쪽 여백(HWPUNIT)으로 줄 폭을 좁힌다
        newp = re.sub(
            r'<hc:right value="-?\d+"', f'<hc:right value="{v["right"]}"', newp
        )
    # numbering: {"text": "^1.", "start": 1, "auto": 1, "offset": 50, "offsetType": "PERCENT", "adjust": 0,
    # "useInst": 1, "align": "LEFT"} — 번호 정의 1 의 1수준 머리를 바꾸고 문단 모양 0 을 그 번호 문단으로 만든다
    nb = v.get("numbering")
    if nb:
        head = re.search(
            r'<hh:paraHead start="\d+" level="1"[^>]*>[^<]*</hh:paraHead>', header
        ).group(0)
        new_head = (
            f'<hh:paraHead start="{nb.get("start", 1)}" level="1" align="{nb.get("align", "LEFT")}" '
            f'useInstWidth="{nb.get("useInst", 1)}" autoIndent="{nb.get("auto", 1)}" '
            f'widthAdjust="{nb.get("adjust", 0)}" textOffsetType="{nb.get("offsetType", "PERCENT")}" '
            f'textOffset="{nb.get("offset", 50)}" numFormat="DIGIT" charPrIDRef="4294967295" '
            f'checkable="0">{escape(nb.get("text", "^1."))}</hh:paraHead>'
        )
        header = header.replace(head, new_head)
        newp = newp.replace(
            '<hh:heading type="NONE" idRef="0" level="0"/>',
            '<hh:heading type="NUMBER" idRef="1" level="0"/>',
        )
    # bullet: {"char": "▶", "auto": 1, "offset": 50, "offsetType": "PERCENT", "adjust": 0, "useInst": 0} — 글머리표 정의 하나를 넣고
    # 문단 모양 0 을 그 글머리표 문단으로 만든다(글머리표 글자 모양은 문단 것)
    bl = v.get("bullet")
    if bl:
        bullet = (
            f'<hh:bullets itemCnt="1"><hh:bullet id="1" char="{escape(bl["char"], {chr(34): "&quot;"})}" useImage="0">'
            f'<hh:paraHead level="0" align="LEFT" useInstWidth="{bl.get("useInst", 0)}" autoIndent="{bl.get("auto", 1)}" '
            f'widthAdjust="{bl.get("adjust", 0)}" textOffsetType="{bl.get("offsetType", "PERCENT")}" '
            f'textOffset="{bl.get("offset", 50)}" numFormat="DIGIT" '
            f'charPrIDRef="{1 if "charHeight" in bl else 4294967295}" checkable="0"/>'
            "</hh:bullet></hh:bullets>"
        )
        assert "<hh:bullets" not in header
        if (
            "charHeight" in bl
        ):  # 글머리표 글자 모양 = charPr 1(크기만 바꾼다, 글꼴은 charPr 0 과 같은 id 1)
            cp1 = re.search(r'<hh:charPr id="1"[\s\S]*?</hh:charPr>', header).group(0)
            header = header.replace(
                cp1,
                re.sub(r'height="\d+"', f'height="{bl["charHeight"]}"', cp1, count=1),
            )
        header = header.replace("</hh:numberings>", "</hh:numberings>" + bullet, 1)
        newp = newp.replace(
            '<hh:heading type="NONE" idRef="0" level="0"/>',
            '<hh:heading type="BULLET" idRef="1" level="0"/>',
        )
    header = header.replace(pp, newp)

    # pageMargin: {"bottom": 3000, ...} — 쪽 여백(HWPUNIT) 바꾸기
    for key, val in (v.get("pageMargin") or {}).items():
        section = re.sub(
            rf'(<hp:margin [^>]*\b{key}=")\d+"', rf'\g<1>{val}"', section, count=1
        )
    paras = v.get("paras") or ["본문 한 문단."]

    # 글 안 특수 요소 표기: ⟦FW⟧ 고정폭 빈칸, ⟦NB⟧ 묶음 빈칸, ⟦HY⟧ 하이픈, ⟦TAB⟧ 탭
    def body(t):
        s = escape(t)
        for k, tag in (
            ("FW", "<hp:fwSpace/>"),
            ("NB", "<hp:nbSpace/>"),
            ("HY", "<hp:hyphen/>"),
            ("TAB", '<hp:tab width="4000" leader="0" type="1"/>'),
        ):
            s = s.replace(f"⟦{k}⟧", tag)
        # ⟦CO:유⟧ 글자 겹치기(동그라미 안 글자). run 안에서 <hp:t> 와 나란한 요소라 글 조각을 닫고 연다
        s = re.sub(
            r"⟦CO:(.)⟧",
            lambda m: (
                '</hp:t><hp:compose circleType="SHAPE_CIRCLE" charSz="-3" composeType="SPREAD" '
                f'charPrCnt="10" composeText="{m.group(1)}">'
                + '<hp:charPr prIDRef="4294967295"/>' * 10
                + "</hp:compose><hp:t>"
            ),
            s,
        )
        return s

    section = section.replace(
        "<hp:t>본문 한 문단.</hp:t>", f"<hp:t>{body(paras[0])}</hp:t>"
    )
    extra = "".join(
        f'<hp:p id="0" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="0"><hp:t>{body(t)}</hp:t></hp:run></hp:p>'
        for t in paras[1:]
    )
    section = section.replace("</hs:sec>", extra + "</hs:sec>")

    out = os.path.join(out_dir, v["name"] + ".hwpx")
    with zipfile.ZipFile(out, "w") as z:
        for info in src.infolist():
            data = src.read(info.filename)
            if info.filename == "Contents/header.xml":
                data = header.encode("utf-8")
            elif info.filename == "Contents/section0.xml":
                data = section.encode("utf-8")
            z.writestr(
                info,
                data,
                compress_type=zipfile.ZIP_STORED
                if info.filename == "mimetype"
                else zipfile.ZIP_DEFLATED,
            )
    return out


def main():
    variants = json.load(open(sys.argv[1], encoding="utf-8"))
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    for v in variants:
        make(v, out_dir)
    print(f"{len(variants)}개 → {out_dir}")


if __name__ == "__main__":
    main()
