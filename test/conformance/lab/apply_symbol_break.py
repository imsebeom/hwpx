"""개발용: 글자 단위 문단에서 기호(㎡ 류, 화살표, ※, 원 숫자, 도형)는 한자처럼 앞뒤 모두 꺾는 자리다.

    python apply_symbol_break.py [--revert]

근거(사본 실험 sb, `exp/make_symbreak.py`, 함초롬바탕, 「가」 32~43개 + 시험 낱말):
- 글자 단위(KEEP_WORD): 「12345678㎡가나다라」 를 한/글은 「12345678|㎡가나」(㎡ 가 넘칠 때), 「12345678㎡|가나」(㎡ 까지 들 때) 로 꺾는다.
  「abcdefgh㎡」, →, ※, ①, ○ 모두 같고, 「가나다라마㎡|123456」, 「가나다라마→|abcdef」 처럼 기호 뒤 라틴, 숫자 앞도 꺾는다.
  「%」 는 숫자에 붙고(라틴 범주), 「℃」 는 줄 머리 금칙이라 앞 숫자와 함께 넘어간다(넣지 않음).
- 엔진은 기호 뒤를 꺾는 자리로 등록하지 않고(한글, 한자만), 숫자와 기호 사이도 막아 낱말 통째로 넘겼다.
- 정답본 d110, d155 「인프라·101.25|㎡ 단일」.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx symbol-break]"
F = "renderer/composer/line_breaking.rs"

# (파일, 찾을 글, 바꿀 글, 자리 수)
EDITS = [
    (
        F,
        "                    } else {\n"
        "                        is_cjk_ideograph(c)\n"
        "                    };\n",
        "                    } else {\n"
        f"                        // {TAG} 글자 단위에서 기호도 뒤를 꺾는 자리로\n"
        "                        is_cjk_ideograph(c) || (korean_break_unit == 1 && claude_symbol_break(c))\n"
        "                    };\n",
        2,
    ),
    (
        F,
        "/// [claude-hwpx latin-hangul-break] `idx` 의 한글 앞이 ASCII 영문자나 숫자라 그 사이에서 줄을 꺾을 수 있는지(「AI를」, 「10문항」).\n",
        f"/// {TAG} 글자 단위에서 한자처럼 앞뒤를 꺾는 기호(사본 실험 sb: ㎡, →, ※, ①, ○). 줄 머리 금칙(℃ 등)과 줄 끝 금칙은 뺀다.\n"
        "fn claude_symbol_break(ch: char) -> bool {\n"
        "    (matches!(ch as u32, 0x3380..=0x33FF | 0x2190..=0x21FF | 0x2460..=0x24FF | 0x25A0..=0x25FF) || ch == '\\u{203B}')\n"
        "        && !is_line_start_forbidden(ch)\n"
        "        && !is_line_end_forbidden(ch)\n"
        "}\n"
        "\n"
        "/// [claude-hwpx latin-hangul-break] `idx` 의 한글 앞이 ASCII 영문자나 숫자라 그 사이에서 줄을 꺾을 수 있는지(「AI를」, 「10문항」).\n",
        1,
    ),
    (
        F,
        "fn claude_latin_hangul_boundary(text_chars: &[char], idx: usize) -> bool {\n"
        "    idx > 0\n",
        "fn claude_latin_hangul_boundary(text_chars: &[char], idx: usize) -> bool {\n"
        f"    // {TAG} 라틴, 숫자 뒤 기호 앞도(「101.25|㎡」)\n"
        "    if idx > 0\n"
        "        && idx < text_chars.len()\n"
        "        && claude_symbol_break(text_chars[idx])\n"
        "        && text_chars[idx - 1].is_ascii_alphanumeric()\n"
        "    {\n"
        "        return true;\n"
        "    }\n"
        "    idx > 0\n",
        1,
    ),
    (
        F,
        "            || ('\\u{2160}'..='\\u{2188}').contains(&text_chars[idx - 1]))\n",
        "            || ('\\u{2160}'..='\\u{2188}').contains(&text_chars[idx - 1])\n"
        f"            // {TAG} 「%」, 「℃」 뒤 한글 앞도(「12345678%|가나」)\n"
        "            || matches!(text_chars[idx - 1], '%' | '\\u{2103}'))\n",
        1,
    ),
]


def main():
    revert = "--revert" in sys.argv
    for rel, find, repl, count in EDITS:
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
        if n != count:
            sys.exit(f"{rel}: 자리 {n}곳(기대 {count}) — {find[:60]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel)


if __name__ == "__main__":
    main()
