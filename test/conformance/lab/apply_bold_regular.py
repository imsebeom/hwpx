"""개발용: 굵은 글자도 보통 글꼴의 폭으로 잰다(그리기는 굵게 그대로).

    python apply_bold_regular.py [--revert]

근거(lab e10, e11): 한/글 2024 PDF 글자 위치로 보통과 굵게를 맞대면 글꼴 8종 중 7종이 글자 폭이 완전히 같고,
굵은 맑은 고딕의 폭은 보통 파일(malgun.ttf) 값과 맞는다(굵은 파일 malgunbd.ttf 보다 약 5% 좁다).
엔진은 굵은 글자에 굵은 얼굴의 폭 표를 써서 넓게 쟀다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx bold-regular-width]"

EDITS = [
    (
        "renderer/layout/text_measurement.rs",
        "        let embedded = measure_char_width_embedded_decision(\n"
        "            &style.font_family,\n"
        "            style.bold,\n",
        f"        // {TAG} 한/글은 굵은 글자도 보통 글꼴의 폭으로 조판한다(test/conformance/lab e10, e11). 그리기만 굵게.\n"
        "        let embedded = measure_char_width_embedded_decision(\n"
        "            &style.font_family,\n"
        "            false,\n",
    ),
]


def main():
    revert = "--revert" in sys.argv
    for rel, find, repl in EDITS:
        if revert:
            find, repl = repl, find
        f = SRC / rel
        raw = f.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        s = raw.replace("\r\n", "\n")
        if (find not in s) if revert else (repl in s):
            print("이미", rel)
            continue
        n = s.count(find)
        if n != 1:
            sys.exit(f"{rel}: 자리 {n}곳 — {find[:50]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel)


if __name__ == "__main__":
    main()
