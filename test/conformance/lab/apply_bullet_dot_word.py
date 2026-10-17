"""개발용: 글자 단위(KEEP_WORD) 문단에서 「•」(U+2022) 바로 뒤 한글의 앞도 꺾는 자리다.

    python apply_bullet_dot_word.py [--revert]

근거(lab e33, 함초롬바탕 10pt, 오른쪽 여백 사다리 29단): KEEP_WORD 에서 한/글은 「마을•체험• | 독서」, 「마을• | 체험」처럼 「•」 뒤에서
꺾고, 「•」가 안 들어가면 「마을 | •체험」처럼 앞에서 꺾는다. 엔진은 「•」를 라틴 낱말로 보는데, 라틴 낱말 뒤 한글 앞은 영문자, 숫자일
때만 꺾는 자리라(latin-hangul-break) 「•」 뒤에서 꺾지 못하고 「•」 앞까지 되돌아갔다(d034/d336 칸). BREAK_WORD 에서는 둘이 같다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx bullet-dot-word]"
LB = "renderer/composer/line_breaking.rs"

EDITS = [
    (
        LB,
        "        && ('가'..='힣').contains(&text_chars[idx])\n        && text_chars[idx - 1].is_ascii_alphanumeric()\n}\n",
        "        && ('가'..='힣').contains(&text_chars[idx])\n"
        f"        // {TAG} 「•」 뒤 한글 앞도 꺾는 자리(lab e33)\n"
        "        && (text_chars[idx - 1].is_ascii_alphanumeric() || text_chars[idx - 1] == '\\u{2022}')\n}\n",
    ),
]


def main():
    revert = "--revert" in sys.argv
    edits = list(reversed(EDITS)) if revert else EDITS
    for rel, find, repl in edits:
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
            sys.exit(f"{rel}: 자리 {n}곳 — {find[:60]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel)


if __name__ == "__main__":
    main()
