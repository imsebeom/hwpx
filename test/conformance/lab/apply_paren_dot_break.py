"""개발용: 글자 단위 문단에서 라틴, 숫자 뒤 「(」 앞(괄호 안이 한글일 때), 가운뎃점 뒤 한글 앞, 로마 숫자 뒤 한글 앞도 꺾는다.

    python apply_paren_dot_break.py [--revert]

근거(사본 실험 pa, pb, `exp/make_paren.py`, 함초롬바탕과 맑은 고딕, 글자 단위, 「가」 32~43개 + 시험 낱말):
- 「abcdefgh(가나다라마)」, 「12345678(가나다라마)」: 한/글은 「(」 까지 줄에 들고 그 뒤 한글이 넘치면 「abcdefgh|(가나」 로 꺾는다.
  「abcdefgh(abcdefg)」 는 한 덩어리(괄호 안이 라틴이면 안 꺾음). 엔진은 라틴 토큰이 「(」 까지 삼켜 낱말 통째로 넘겼다.
- 「(」 자체가 넘치면 그 앞을 쓰지 않고 앞 빈칸으로 돌아간다(실험 pc, `exp/make_paren2.py`, d110 「Operation Zone(교사」 재현:
  「Zone(」 끝 44380 ≤ 45688 이면 「Zone|(」, 「Zone」 끝 45380 은 들지만 「(」 끝 45880 이 넘치면 「|Zone(」). 그래서 「(」 토큰이
  줄에 든 뒤에만 그 앞을 꺾을 자리로 등록한다.
- 「ABCDE·가나다라마바」: 한/글 「ABCDE·|가나」. 「ABCDE·FGHIJKL」 은 한 덩어리(dot-latin-glue 그대로).
- 「가나다(Ⅲ가나다라마)」: 한/글 「(Ⅲ|가나」. 엔진은 「|(Ⅲ」.
- 정답본 d229 「chamber|(이중」, d155 「AI·|컴퓨터」, d122 「(Ⅲ|단계」, d333 「7/25|(화)」.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx paren-dot-break]"
F = "renderer/composer/line_breaking.rs"

REG = (
    f"                // {TAG} 라틴, 숫자 뒤 「(」(괄호 안이 한글)는 「(」 까지 줄에 들 때만 그 앞을 꺾을 자리로(실험 pc)\n"
    "                if korean_break_unit == 1\n"
    "                    && token_fits\n"
    "                    && ti > 0\n"
    "                    && *start_idx > {LS}\n"
    "                    && claude_latin_paren_boundary(text_chars, *start_idx)\n"
    "                {\n"
    "                    {P}last_break_token_idx = Some(ti - 1);\n"
    "                    {P}last_break_char_idx = *start_idx;\n"
    "                    {P}width_at_last_break = {P}lw;\n"
    "                    {P}space_savings_at_last_break = {P}line_space_savings;\n"
    "                    {P}fs_at_last_break = {P}line_max_fs;\n"
    "                }\n"
)

EDITS = [
    (
        F,
        "                    if !is_latin(c) && !is_lang_neutral(c) {\n"
        "                        break;\n"
        "                    }\n"
        "                    // 하이픈 모드: 하이픈에서 분할 (하이픈 포함 후 분리)\n",
        "                    if !is_latin(c) && !is_lang_neutral(c) {\n"
        "                        break;\n"
        "                    }\n"
        f"                    // {TAG} 글자 단위에서 괄호 안이 한글이면 「(」 앞에서 토큰을 끊는다(그 앞이 꺾을 자리)\n"
        "                    if korean_break_unit == 1\n"
        "                        && c == '('\n"
        "                        && !token_text.is_empty()\n"
        "                        && i + 1 < text_len\n"
        "                        && ('가'..='힣').contains(&text_chars[i + 1])\n"
        "                    {\n"
        "                        break;\n"
        "                    }\n"
        "                    // 하이픈 모드: 하이픈에서 분할 (하이픈 포함 후 분리)\n",
    ),
    (
        F,
        "                        cursor.fs_at_last_break = cursor.line_max_fs;\n"
        "                    }\n"
        "                }\n"
        "                if !token_fits {\n",
        "                        cursor.fs_at_last_break = cursor.line_max_fs;\n"
        "                    }\n"
        "                }\n"
        + REG.replace("{LS}", "cursor.line_start_idx").replace("{P}", "cursor.")
        + "                if !token_fits {\n",
    ),
    (
        F,
        "                        fs_at_last_break = line_max_fs;\n"
        "                    }\n"
        "                }\n"
        "                if !text_token_fits_line_hwp(\n",
        "                        fs_at_last_break = line_max_fs;\n"
        "                    }\n"
        "                }\n"
        + REG.replace("{LS}", "line_start_idx").replace("{P}", "")
        + "                if !text_token_fits_line_hwp(\n",
    ),
    (
        F,
        "/// [claude-hwpx latin-hangul-break] `idx` 의 한글 앞이 ASCII 영문자나 숫자라 그 사이에서 줄을 꺾을 수 있는지(「AI를」, 「10문항」).\n",
        f"/// {TAG} `idx` 가 「(」 이고 그 앞이 ASCII 영문자나 숫자, 뒤가 한글인지(「chamber|(이중」, 「7/25|(화)」)\n"
        "fn claude_latin_paren_boundary(text_chars: &[char], idx: usize) -> bool {\n"
        "    idx > 0\n"
        "        && idx + 1 < text_chars.len()\n"
        "        && text_chars[idx] == '('\n"
        "        && ('가'..='힣').contains(&text_chars[idx + 1])\n"
        "        && text_chars[idx - 1].is_ascii_alphanumeric()\n"
        "}\n"
        "\n"
        "/// [claude-hwpx latin-hangul-break] `idx` 의 한글 앞이 ASCII 영문자나 숫자라 그 사이에서 줄을 꺾을 수 있는지(「AI를」, 「10문항」).\n",
    ),
    (
        F,
        "                ']' | ')' | '}' | '\\'' | '/' | ',' | '-' | '\\u{300D}' | '\\u{300F}' | '\\u{2019}' | '\\u{201D}'\n"
        "            ))\n",
        "                ']' | ')' | '}' | '\\'' | '/' | ',' | '-' | '\\u{300D}' | '\\u{300F}' | '\\u{2019}' | '\\u{201D}'\n"
        "            )\n"
        f"            // {TAG} 가운뎃점 뒤(「AI·|컴퓨터」), 로마 숫자 뒤(「(Ⅲ|단계」) 한글 앞도\n"
        "            || matches!(text_chars[idx - 1], '\\u{00B7}' | '\\u{30FB}' | '\\u{FF65}' | '\\u{2027}' | '\\u{2219}')\n"
        "            || ('\\u{2160}'..='\\u{2188}').contains(&text_chars[idx - 1]))\n",
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
            sys.exit(f"{rel}: 자리 {n}곳 — {find[:60]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel)


if __name__ == "__main__":
    main()
