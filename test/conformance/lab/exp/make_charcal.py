"""글자 폭 보정표 실험 문서: d050 사본(줄 배치 지움) 본문을 (글꼴 x 장평, 자간) 변형마다 왼쪽 정렬 문단 하나로 바꾼다.
문단마다 「◆NN◆」 표지 뒤에 시험 글자를 8개씩 이어 쓴다(글자 사이 「|」). read_charcal.py 가 한/글 PDF 와 엔진 SVG 에서
같은 글자 8개 묶음의 평균 전진 폭을 견준다.

    python exp/make_charcal.py ../out/fresh/in/d050.hwpx <출력 폴더>
"""

import copy
import re
import sys
import zipfile
from pathlib import Path

from lxml import etree

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
FONTS = {
    "함초롬바탕": 6,
    "함초롬돋움": 5,
    "맑은 고딕": 2,
    "휴먼명조": 7,
    "굴림": 0,
    "바탕": 3,
}
STYLES = [(100, 0), (100, -5), (95, 0), (90, -10)]
CHARS = "()[]\"'.,:;-·1234567890ABIa가생사시점호「」▪※①"
SIZE = 1000

src, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
zin = zipfile.ZipFile(src)
parts = {i.filename: zin.read(i.filename) for i in zin.infolist()}
infos = zin.infolist()

h = parts["Contents/header.xml"].decode("utf-8")
n_char = int(re.search(r'<hh:charProperties itemCnt="(\d+)"', h).group(1))
n_para = int(re.search(r'<hh:paraProperties itemCnt="(\d+)"', h).group(1))
base_cp = re.search(r'<hh:charPr id="0"[\s\S]*?</hh:charPr>', h).group(0)
base_pp = re.search(r'<hh:paraPr id="0"[\s\S]*?</hh:paraPr>', h).group(0)

variants = []
new_cps = []
for font, fid in FONTS.items():
    for ratio, spacing in STYLES:
        cid = n_char + len(variants)
        cp = re.sub(r'id="0"', f'id="{cid}"', base_cp, count=1)
        cp = re.sub(r'height="\d+"', f'height="{SIZE}"', cp, count=1)
        cp = re.sub(
            r"<hh:fontRef [^>]*/>",
            f'<hh:fontRef hangul="{fid}" latin="{fid}" hanja="{fid}" japanese="{fid}" other="{fid}" symbol="{fid}" user="{fid}"/>',
            cp,
        )
        cp = re.sub(
            r"<hh:ratio [^>]*/>",
            f'<hh:ratio hangul="{ratio}" latin="{ratio}" hanja="{ratio}" japanese="{ratio}" other="{ratio}" symbol="{ratio}" user="{ratio}"/>',
            cp,
        )
        cp = re.sub(
            r"<hh:spacing [^>]*/>",
            f'<hh:spacing hangul="{spacing}" latin="{spacing}" hanja="{spacing}" japanese="{spacing}" other="{spacing}" symbol="{spacing}" user="{spacing}"/>',
            cp,
        )
        cp = re.sub(r'useFontSpace="\d"', 'useFontSpace="0"', cp)
        new_cps.append(cp)
        variants.append((font, ratio, spacing, cid))
pid = n_para
pp = re.sub(r'id="0"', f'id="{pid}"', base_pp, count=1)
pp = re.sub(r'<hh:align horizontal="\w+"', '<hh:align horizontal="LEFT"', pp)
pp = re.sub(r'<hc:(intent|left|right|prev|next) value="-?\d+"', r'<hc:\1 value="0"', pp)
h = h.replace("</hh:charProperties>", "".join(new_cps) + "</hh:charProperties>")
h = re.sub(
    r'<hh:charProperties itemCnt="\d+"',
    f'<hh:charProperties itemCnt="{n_char + len(new_cps)}"',
    h,
)
h = h.replace("</hh:paraProperties>", pp + "</hh:paraProperties>")
h = re.sub(
    r'<hh:paraProperties itemCnt="\d+"', f'<hh:paraProperties itemCnt="{n_para + 1}"', h
)

root = etree.fromstring(parts["Contents/section0.xml"])
ps = [p for p in root if p.tag == f"{HP}p"]
first = copy.deepcopy(ps[0])
for p in ps:
    root.remove(p)
for r in first.findall(f"{HP}run"):
    for el in list(r):
        if etree.QName(el).localname not in ("secPr", "ctrl"):
            r.remove(el)
for la in first.findall(f"{HP}linesegarray"):
    first.remove(la)
first.set("paraPrIDRef", str(pid))
root.append(first)
for k, (font, ratio, spacing, cid) in enumerate(variants):
    p = etree.SubElement(
        root,
        f"{HP}p",
        id="0",
        paraPrIDRef=str(pid),
        styleIDRef="0",
        pageBreak="0",
        columnBreak="0",
        merged="0",
    )
    run = etree.SubElement(p, f"{HP}run", charPrIDRef=str(cid))
    t = etree.SubElement(run, f"{HP}t")
    t.text = f"◆{k:02d}◆" + "|".join(c * 8 for c in CHARS) + "|가 가 가 가 가 가 가 가"
parts["Contents/header.xml"] = h.encode("utf-8")
parts["Contents/section0.xml"] = etree.tostring(
    root, xml_declaration=True, encoding="UTF-8", standalone=True
)
with zipfile.ZipFile(out / "charcal.hwpx", "w", zipfile.ZIP_DEFLATED) as z:
    for info in infos:
        z.writestr(
            zipfile.ZipInfo(info.filename),
            parts[info.filename],
            compress_type=zipfile.ZIP_STORED
            if info.filename == "mimetype"
            else zipfile.ZIP_DEFLATED,
        )
(out / "variants.txt").write_text(
    "\n".join(f"{k:02d}\t{f}\t{r}\t{s}" for k, (f, r, s, _) in enumerate(variants)),
    encoding="utf-8",
)
print("ok", len(variants))
