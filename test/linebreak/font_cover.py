"""대조 문서 317개에서 글자가 쓰는 글꼴(한글 글꼴 기준)을 세고, 엔진 폭 자료 유무와 이 PC 설치 여부로 나눈다."""

import json
import re
import sys
import zipfile
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
RHWP = r"C:\Users\hccga\.claude\skills\hwpx\editor\.build\rhwp\src\renderer"
engine = {
    line.split("	", 1)[1].strip()
    for line in open("corpus_faces_metric.tsv", encoding="utf-8")
    if line.startswith("1")
}
installed = set()
for e in json.load(open("fonts_index.json", encoding="utf-8")):
    installed |= {n.lower() for n in e.get("names", [])}

chars = Counter()
docs = Counter()
for path in open("reg_corpus.txt", encoding="utf-8").read().splitlines():
    path = path.strip()
    try:
        z = zipfile.ZipFile(path)
        hdr = z.read("Contents/header.xml").decode("utf-8")
    except Exception:
        continue
    m = re.search(r'<hh:fontface lang="HANGUL"[^>]*>(.*?)</hh:fontface>', hdr, re.S)
    faces = (
        dict(re.findall(r'<hh:font id="(\d+)" face="([^"]*)"', m.group(1))) if m else {}
    )
    char_face = {}
    for cid, body in re.findall(
        r'<hh:charPr id="(\d+)"[^>]*>(.*?)</hh:charPr>', hdr, re.S
    ):
        ref = re.search(r'<hh:fontRef hangul="(\d+)"', body)
        char_face[cid] = faces.get(ref.group(1), "?") if ref else "?"
    seen = set()
    for name in z.namelist():
        if not re.match(r"Contents/section\d+\.xml", name):
            continue
        sec = z.read(name).decode("utf-8")
        for cid, run in re.findall(
            r'<hp:run charPrIDRef="(\d+)"[^>]*>(.*?)</hp:run>', sec, re.S
        ):
            n = sum(len(t) for t in re.findall(r"<hp:t\b[^>]*>([^<]*)</hp:t>", run))
            if n:
                face = char_face.get(cid, "?")
                chars[face] += n
                seen.add(face)
    for face in seen:
        docs[face] += 1

total = sum(chars.values())
groups = {
    "엔진 자료 있음": Counter(),
    "자료 없음, 이 PC 에 설치됨": Counter(),
    "자료 없음, 설치도 안 됨": Counter(),
}
for face, n in chars.items():
    if face in engine:
        groups["엔진 자료 있음"][face] = n
    elif face.lower() in installed:
        groups["자료 없음, 이 PC 에 설치됨"][face] = n
    else:
        groups["자료 없음, 설치도 안 됨"][face] = n
print(
    "엔진 폭 자료 글꼴",
    len(engine),
    "| 이 PC 글꼴 이름",
    len(installed),
    "| 문서 글자",
    total,
)
for label, c in groups.items():
    print(
        f"\n{label}: 글꼴 {len(c)}종, 글자 {sum(c.values())} ({sum(c.values()) / total:.1%})"
    )
    for face, n in c.most_common(14):
        print(f"   {face:<24} 글자 {n:>8} ({n / total:.2%}) 문서 {docs[face]}")
