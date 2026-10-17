"""개발용: 라틴 글자나 숫자 바로 뒤에 붙은 한글 앞에서도 줄을 꺾을 수 있게 한다(「생성형 AI」 / 「를 붙일 때」).

    python apply_latin_hangul_break.py [--revert]

근거(정답본 줄 기록): 한/글은 「AI를」, 「10문항」, 「PC에서」처럼 빈칸 없이 붙은 라틴, 숫자와 한글 사이에서 줄을 꺾는다.
줄 나눔 기준이 글자 단위(KEEP_WORD)인 문단에서 97곳이다. 어절 단위(BREAK_WORD)의 42곳은 칸보다 긴 어절을 억지로 자른
자리라(「기본10|만원~20만원+…」, 「[12인기04-0|1]」) 글자 단위 문단에만 넣는다.
엔진은 라틴 단어 토큰과 뒤 한글 사이를 꺾을 자리로 보지 않아 「AI를」을 통째로 다음 줄로 넘겼다(d193).
여는 괄호, 따옴표 뒤의 한글은 줄 끝 금칙이라 넣지 않는다(앞 글자가 ASCII 영문자나 숫자일 때만).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx latin-hangul-break]"
REL = "renderer/composer/line_breaking.rs"

EDITS = [
    (
        REL,
        "fn recalc_width_hwp(tokens: &[BreakToken], current_token_idx: usize, new_line_start: usize) -> i32 {\n",
        f"/// {TAG} `idx` 의 한글 앞이 ASCII 영문자나 숫자라 그 사이에서 줄을 꺾을 수 있는지(「AI를」, 「10문항」).\n"
        "fn claude_latin_hangul_boundary(text_chars: &[char], idx: usize) -> bool {\n"
        "    idx > 0\n"
        "        && idx < text_chars.len()\n"
        "        && ('가'..='힣').contains(&text_chars[idx])\n"
        "        && text_chars[idx - 1].is_ascii_alphanumeric()\n"
        "}\n"
        "\n"
        "fn recalc_width_hwp(tokens: &[BreakToken], current_token_idx: usize, new_line_start: usize) -> i32 {\n",
    ),
    (
        REL,
        "                claude_note_token_start(text_chars, *start_idx);\n"
        "                if let Some(next_char_idx) = cursor.fallback_char_idx {\n",
        "                claude_note_token_start(text_chars, *start_idx);\n"
        "                // [claude-hwpx latin-hangul-break] 라틴, 숫자 바로 뒤 한글의 앞도 꺾을 자리다\n"
        "                if cursor.fallback_char_idx.is_none()\n"
        "                    && korean_break_unit == 1\n"
        "                    && ti > 0\n"
        "                    && *start_idx > cursor.line_start_idx\n"
        "                    && claude_latin_hangul_boundary(text_chars, *start_idx)\n"
        "                {\n"
        "                    cursor.last_break_token_idx = Some(ti - 1);\n"
        "                    cursor.last_break_char_idx = *start_idx;\n"
        "                    cursor.width_at_last_break = cursor.lw;\n"
        "                    cursor.space_savings_at_last_break = cursor.line_space_savings;\n"
        "                    cursor.fs_at_last_break = cursor.line_max_fs;\n"
        "                }\n"
        "                if let Some(next_char_idx) = cursor.fallback_char_idx {\n",
    ),
    (
        REL,
        "                claude_note_token_start(text_chars, *start_idx);\n"
        "                if *max_font_size > line_max_fs {\n",
        "                claude_note_token_start(text_chars, *start_idx);\n"
        "                // [claude-hwpx latin-hangul-break] 운영 경로와 같게(동등성 시험용 사본)\n"
        "                if korean_break_unit == 1\n"
        "                    && ti > 0\n"
        "                    && *start_idx > line_start_idx\n"
        "                    && claude_latin_hangul_boundary(text_chars, *start_idx)\n"
        "                {\n"
        "                    last_break_token_idx = Some(ti - 1);\n"
        "                    last_break_char_idx = *start_idx;\n"
        "                    width_at_last_break = lw;\n"
        "                    space_savings_at_last_break = line_space_savings;\n"
        "                    fs_at_last_break = line_max_fs;\n"
        "                }\n"
        "                if *max_font_size > line_max_fs {\n",
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
            sys.exit(f"{rel}: 자리 {n}곳 — {find[:50]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel)


if __name__ == "__main__":
    main()
