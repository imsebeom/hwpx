"""개발용: 가운뎃점 바로 뒤가 라틴 글자나 숫자면 가운뎃점 뒤에서 줄을 꺾지 않는다.

    python apply_dot_latin_glue.py [--revert]

근거(새 정답본 327문서, 조판 부호 없는 문단): 가운뎃점(· ・ ･ ‧ ∙) 다음 글자가 ASCII 영문자나 숫자인 자리 307곳(H·L 125, L·L 182)에서
한/글은 가운뎃점 앞에서도 뒤에서도 한 번도 꺾지 않았다. 다음이 한글이면(H·H 3,690곳) 가운뎃점 뒤에서 86번 꺾는다.
엔진은 글자 단위 문단에서 「록·」(한글 + 줄 머리 금칙 문자) 뒤를 꺾을 자리로 등록해 「블록·|AI」, 「조도·|CO2」 로 나눴고,
한/글은 「블|록·AI」, 「조|도·CO2」 로 나눈다(d110, d155). 가운뎃점 앞은 이미 줄 머리 금칙이다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx dot-latin-glue]"

REG_OLD = (
    "                    if allow_break {\n"
    "                        cursor.last_break_token_idx = Some(ti);\n"
    "                        cursor.last_break_char_idx = *end_idx; // 이 글자 다음 (이 글자 포함)\n"
)
REG_NEW = (
    "                    if allow_break && !claude_dot_latin_glue(text_chars, *end_idx) {\n"
    "                        cursor.last_break_token_idx = Some(ti);\n"
    "                        cursor.last_break_char_idx = *end_idx; // 이 글자 다음 (이 글자 포함)\n"
)
MIRROR_OLD = (
    "                    if allow_break {\n"
    "                        last_break_token_idx = Some(ti);\n"
    "                        last_break_char_idx = *end_idx; // 이 글자 다음 (이 글자 포함)\n"
)
MIRROR_NEW = (
    "                    if allow_break && !claude_dot_latin_glue(text_chars, *end_idx) {\n"
    "                        last_break_token_idx = Some(ti);\n"
    "                        last_break_char_idx = *end_idx; // 이 글자 다음 (이 글자 포함)\n"
)

EDITS = [
    (
        "renderer/composer/line_breaking.rs",
        "pub(crate) fn is_line_end_forbidden(ch: char) -> bool {\n",
        f"/// {TAG} `idx` 앞 글자가 가운뎃점이고 `idx` 가 ASCII 영문자나 숫자면 그 사이는 꺾지 않는다.\n"
        "/// 한/글 새 정답본 327문서에서 가운뎃점 뒤가 라틴인 307곳 모두 가운뎃점 앞뒤로 꺾지 않았다(「블|록·AI」).\n"
        "fn claude_dot_latin_glue(text_chars: &[char], idx: usize) -> bool {\n"
        "    idx > 0\n"
        "        && idx < text_chars.len()\n"
        "        && text_chars[idx].is_ascii_alphanumeric()\n"
        "        && matches!(\n"
        "            text_chars[idx - 1],\n"
        "            '\\u{00B7}' | '\\u{30FB}' | '\\u{FF65}' | '\\u{2027}' | '\\u{2219}'\n"
        "        )\n"
        "}\n"
        "\n"
        "pub(crate) fn is_line_end_forbidden(ch: char) -> bool {\n",
    ),
    ("renderer/composer/line_breaking.rs", REG_OLD, REG_NEW),
    ("renderer/composer/line_breaking.rs", MIRROR_OLD, MIRROR_NEW),
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
