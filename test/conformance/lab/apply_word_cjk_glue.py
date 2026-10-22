"""개발용: 어절 단위 문단의 한글 낱말은 한자, 일본 문자(・ 등)에서 끊지 않고, 글자 단위에서 ・ 는 줄 머리 금칙이다.

    python apply_word_cjk_glue.py [--revert]

근거(사본 실험 cj, gg — scratchpad, 함초롬바탕, 맑은 고딕):
- 어절 단위(breakNonLatinWord=BREAK_WORD): 「가・」x30, 「가漢」x30, 「가가가・」x15, 「가가가漢」x15, 「漢가가가」x15 모두 한/글은 43자(글자
  단위로 꽉 채움)다. 빈칸 없는 묶음 전체를 한 낱말로 보고, 줄보다 길어 글자 단위로 채운다. 엔진은 한자와 ・ 에서 낱말을 끊어
  그 경계에서만 꺾어 40~42자였다. 정답본 d336 「독서·토론・인|문교육」, 「세계시민・다|문화・통일교|육」 이 같은 꼴(엔진은
  「토론・|인문교육」). 정답본 어절 단위 문단의 한글-한자 경계 28곳에서 한/글이 꺾은 곳은 0.
- 글자 단위(KEEP_WORD): 「가・」x30 과 「가가가・」x15 를 한/글은 42자로 꺾는다(・ 가 줄 머리에 오지 않게 앞 글자와 함께 내림).
  엔진은 43자.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx word-cjk-glue]"

EDITS = [
    (
        "renderer/composer/line_breaking.rs",
        "                    // CJK 한자/일본어는 개별 토큰\n"
        "                    if is_cjk_ideograph(c) {\n"
        "                        break;\n"
        "                    }\n",
        f"                    // {TAG} 한/글은 어절 단위에서 빈칸 없는 한글, 한자, 일본 문자 묶음을 한 낱말로 본다\n"
        "                    // (사본 실험: 「가漢」, 「가・」 반복이 낱말 하나로 글자 단위 채움, d336 「토론・인|문교육」)\n",
    ),
    (
        "renderer/composer/line_breaking.rs",
        "            | '\\u{00B7}'\n            | '\\u{2015}'\n",
        "            | '\\u{00B7}'\n"
        f"            // {TAG} ・ 도 줄 머리에 오지 않는다(글자 단위 사본 실험 「가・」, 「가가가・」)\n"
        "            | '\\u{30FB}'\n"
        "            | '\\u{2015}'\n",
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
