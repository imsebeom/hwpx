"""글꼴 파일의 폭(hmtx)으로 한/글 예상 폭을 내 세 글꼴 사다리를 만든다: wl5.json, wl5.charpr.json"""
import json, math, os, sys
from fontTools.ttLib import TTFont
sys.stdout.reconfigure(encoding="utf-8")
FILES = {"한컴산뜻돋움": r"C:\Windows\Fonts\HanSantteutDotum-Regular.ttf", "나눔스퀘어": r"C:\Windows\Fonts\NanumSquareR.ttf", "한컴 고딕": r"C:\Windows\Fonts\Hancom Gothic Regular.ttf"}
P = "가 "
SET = ["가" * 10, "가 가 가 가 가 가", P + "0" * 10, P + "a" * 10, P + "A" * 10, P + "(" * 10, P + "." * 10, P + "·" * 10, P + "「" * 10, P + "~" * 10, "가0가0가0가0가0", "(가)(가)(가)(가)"]
adv = {}
for face, path in FILES.items():
    f = TTFont(path); cm = f.getBestCmap(); hm = f["hmtx"]; upm = f["head"].unitsPerEm
    adv[face] = lambda ch, cm=cm, hm=hm, upm=upm: hm[cm[ord(ch)]][0] / upm
def units(face, text, em):
    total = 0
    for ch in text:
        total += math.floor(em / 2 + 1e-6) if ch == " " else math.floor(adv[face](ch) * em + 0.5 + 1e-6)
    return total
variants, spec = [], []
cid = 50
for face in FILES:
    for h in (1000, 1100, 1200) if face != "한컴 고딕" else (1000,):
        variants.append(dict(id=cid, height=h, face=face, bold=False))
        for t in SET:
            u = units(face, t, h / 4)
            spec.append(dict(text=t, char=cid, est=u * 4, span=40, v=dict(face=face, height=h), pred=u))
        cid += 1
json.dump(spec, open("wl5.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(dict(fonts=list(FILES), variants=variants), open("wl5.charpr.json", "w", encoding="utf-8"), ensure_ascii=False)
print(len(spec), len(variants))
