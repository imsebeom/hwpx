"""설치되지 않은 글꼴을 한/글이 무엇으로 바꿔 그리는지 보는 실험 문서(make.py 변형 json 을 만든다).

    python exp/make_fallback.py <출력 폴더>   → <출력>/fb.json, fc.json
    python make.py <출력>/fb.json <입력 폴더>; python make.py <출력>/fc.json <입력 폴더>
    → hwpx_lab/measure.py → PDF 글꼴 이름(fitz get_fonts, rawdict span font)과 pdfadv.py / rhwpadv.mjs / cmpadv.py

fb: 같은 글(한글, 라틴, 숫자, 기호)을 함초롬바탕, 한컴바탕, 없는 이름, KoPubWorld바탕체 Bold, Noto Serif CJK SC 로.
fc: 없는 이름 글꼴로 e20 기호 160자 + 한자, 확장 라틴, 자모를 「가X가X」 꼴로.
결과(2026-10-22): 없는 글꼴은 고딕 분류여도 PDF 글꼴이 Haansoft Batang(한컴바탕)이고, 라틴(U+0250 미만), ‘’“”, 한글 자모,
・･ 밖의 기호와 한자는 HCRBatang(함초롬바탕)으로 찍힌다. 한컴바탕(TTF 이름) 문서도 같다.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)

paras = [
    "가나다라마바사아자차카타파하 한글 문장의 폭을 재는 줄입니다. 서울특별시교육청 학생 평가 계획",
    "The quick brown fox jumps over the lazy dog 0123456789 ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "※ … · • ① → 「」 『』 ( ) [ ] , . : ; ! ? % ~ - — ' \" ○ □ ■ ▶ ㉠",
] * 3
fonts = [
    ("hcr", "함초롬바탕"),
    ("han", "한컴바탕"),
    ("none", "없는글꼴가나다"),
    ("kopub", "KoPubWorld바탕체 Bold"),
    ("noto", "Noto Serif CJK SC"),
]
fb = [{"name": f"fb_{k}", "face": f, "align": "LEFT", "paras": paras} for k, f in fonts]
(out / "fb.json").write_text(json.dumps(fb, ensure_ascii=False), encoding="utf-8")

chars = json.loads((HERE / "e20_meta.json").read_text(encoding="utf-8"))["chars"]
chars += "漢字學校敎育ÀéñüßŁőĀ½¼±×÷§°¶©®™€£¥ㄱㅏ"
chars = "".join(dict.fromkeys(chars))
fc_paras = [
    "가" + "가".join(chars[i : i + 20]) + "가" for i in range(0, len(chars), 20)
]
fc = [{"name": "fc_none", "face": "없는글꼴가나다", "align": "LEFT", "paras": fc_paras}]
(out / "fc.json").write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
print("ok", len(chars))
