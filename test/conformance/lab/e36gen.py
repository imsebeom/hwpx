"""e36: 1단 구역에서 단 나누기(columnBreak=1) 문단이 새 쪽을 여는가. 글 문단, 빈 문단, 다음 문단이 쪽 나눔인 경우(d058 p12)."""

import json

L = ("HANGUL", "LATIN", "HANJA", "JAPANESE", "OTHER", "SYMBOL", "USER")
CASES = {
    "A": ["첫째 문단", "둘째 문단", "[[CB]]셋째 단나누기 글", "넷째 문단"],
    "B": ["첫째 문단", "둘째 문단", "[[CB]]", "넷째 문단"],
    "C": ["첫째 문단", "둘째 문단", "[[CB]]", "[[PB]]넷째 쪽나눔"],
    "D": ["첫째 문단", "둘째 문단", "[[CB]]셋째 단나누기 글", "[[PB]]넷째 쪽나눔"],
}
out = [{"name": f"e36_{k}", "langFaces": {x: "함초롬바탕" for x in L}, "height": 1000, "align": "LEFT", "paras": v} for k, v in CASES.items()]
json.dump(out, open("e36.json", "w", encoding="utf-8"), ensure_ascii=False)
print(len(out))
