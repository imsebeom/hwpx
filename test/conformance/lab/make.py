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
        header = header.replace(
            block,
            re.sub(r'(<hh:font id="1" face=")[^"]*"', rf'\g<1>{escape(face)}"', block),
        )
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
    header = header.replace(pp, newp)

    # pageMargin: {"bottom": 3000, ...} — 쪽 여백(HWPUNIT) 바꾸기
    for key, val in (v.get("pageMargin") or {}).items():
        section = re.sub(
            rf'(<hp:margin [^>]*\b{key}=")\d+"', rf'\g<1>{val}"', section, count=1
        )
    paras = v.get("paras") or ["본문 한 문단."]
    section = section.replace(
        "<hp:t>본문 한 문단.</hp:t>", f"<hp:t>{escape(paras[0])}</hp:t>"
    )
    extra = "".join(
        f'<hp:p id="0" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="0"><hp:t>{escape(t)}</hp:t></hp:run></hp:p>'
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
