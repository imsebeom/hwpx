"""엔진이 첫 줄을 한/글보다 먼저 꺾는 불일치(본문, 칸)를 문단 모양과 글자 모양 속성별로 센다.

    python earlystat.py <불일치.jsonl>

속성: 정렬, 빈칸 줄이기(condense), 영문/한글 낱말 나눔, 첫 run 글꼴(한글), 장평, 자간. 한/글과 엔진의 둘째 줄 시작 차이(글자 수)도 본다.
"""

import collections
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
from headstat import load  # noqa: E402


def attrs(p, h):
    pid = re.search(r'paraPrIDRef="(\d+)"', p).group(1)
    pp = re.search(rf'<hh:paraPr id="{pid}"[\s\S]*?</hh:paraPr>', h).group(0)
    align = re.search(r'<hh:align horizontal="(\w+)"', pp).group(1)
    condense = re.search(r'condense="(\d+)"', pp).group(1)
    blw = re.search(r'breakLatinWord="(\w+)"', pp).group(1)
    bnw = re.search(r'breakNonLatinWord="(\w+)"', pp).group(1)
    runs = re.findall(r'<hp:run charPrIDRef="(\d+)"', p)
    cid = runs[0] if runs else "0"
    cp = re.search(rf'<hh:charPr id="{cid}"[\s\S]*?</hh:charPr>', h).group(0)
    ratio = re.search(r'<hh:ratio hangul="(\d+)"', cp).group(1)
    spacing = re.search(r'<hh:spacing hangul="(-?\d+)"', cp).group(1)
    font_id = re.search(r'<hh:fontRef hangul="(\d+)"', cp).group(1)
    fs = re.search(r'<hh:fontface lang="HANGUL"[\s\S]*?</hh:fontface>', h).group(0)
    face = re.search(rf'<hh:font id="{font_id}" face="([^"]+)"', fs)
    return {
        "정렬": align,
        "빈칸줄이기": condense,
        "영문": blw,
        "한글": bnw,
        "장평": ratio,
        "자간": spacing,
        "글꼴": face.group(1) if face else "?",
    }


def main(path):
    rows = [json.loads(line) for line in open(path, encoding="utf-8")]
    cache = {}
    counts = collections.defaultdict(collections.Counter)
    n = 0
    for r in rows:
        han, rh = r["han"], r["rhwp"]
        if len(han) < 2 or len(rh) < 2 or not (rh[1] < han[1]):
            continue
        body, cells, h = load(r["id"], cache)
        try:
            p = body[r["para"]] if r["where"] == "본문" else cells[r["cell"]][r["para"]]
        except (IndexError, ValueError, KeyError):
            continue
        a = attrs(p, h)
        a["차(글자)"] = str(min(han[1] - rh[1], 5))
        for k, v in a.items():
            counts[k][v] += 1
        n += 1
    print("엔진이 첫 줄을 먼저 꺾은 문단", n)
    for k, c in counts.items():
        print(f"  {k}: " + ", ".join(f"{v} {cnt}" for v, cnt in c.most_common(8)))


if __name__ == "__main__":
    main(sys.argv[1])
