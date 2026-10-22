"""개발용: 전각 빈칸(U+3000)을 빈칸처럼 다룬다 — 그 뒤에서 꺾고, 줄 끝에서는 앞줄에 매단다.

    python apply_ideographic_space.py [--revert]

근거(새 정답본): 한/글은 전각 빈칸 바로 앞에서 꺾지 않고(한글 뒤 18곳 중 0), 뒤에서 꺾는다(「　|-」 3/5). d266 「제안서 발표　|- 데이터」,
「루브릭 평가　|(기능」, d214 「소리　　|　그림자」(묶음 처음 두 칸은 앞줄). 엔진은 전각 빈칸을 보통 글자로 보아 다음 줄 머리에 두었다.
폭은 빈칸 규칙(space_advance)이 아니라 그 글꼴의 전각 빈칸 폭으로 잰다. 새 정답본 불일치 187 → 184, 새로 틀린 줄 0.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx ideographic-space]"
SKIP_OLD = "while next_start < text_chars.len() && text_chars[next_start] == ' ' {\n"
SKIP_NEW = "while next_start < text_chars.len() && matches!(text_chars[next_start], ' ' | '\\u{3000}') {\n"
LIVE = "                            let mut next_start = cursor.last_break_char_idx;\n                            "
MIRROR = "                            let mut next_start = last_break_char_idx;\n                            "

EDITS = [
    (
        "renderer/composer/line_breaking.rs",
        "        // 공백 (줄 바꿈 지점) — NonBreakingSpace(\\u{00A0})는 제외\n        if ch == ' ' {\n",
        f"        // {TAG} 전각 빈칸은 빈칸처럼 꺾고 줄 끝에 매단다. 폭은 그 글꼴의 전각 빈칸 폭\n"
        "        if ch == '\\u{3000}' {\n"
        "            let utf16_pos = if i < char_offsets.len() {\n"
        "                char_offsets[i]\n"
        "            } else {\n"
        "                i as u32\n"
        "            };\n"
        "            let style_id = find_active_char_shape(char_shapes, utf16_pos);\n"
        "            let ts = resolved_to_text_style(styles, style_id, current_lang);\n"
        "            let font_size = if ts.font_size > 0.0 { ts.font_size } else { 12.0 };\n"
        '            let w = estimate_text_width_unrounded("\\u{3000}", &ts) + inline_width_px_at(inline_controls, i);\n'
        "            tokens.push(BreakToken::Space {\n"
        "                idx: i,\n"
        "                width: w,\n"
        "                max_font_size: font_size,\n"
        "            });\n"
        "            i += 1;\n"
        "            continue;\n"
        "        }\n"
        "\n"
        "        // 공백 (줄 바꿈 지점) — NonBreakingSpace(\\u{00A0})는 제외\n        if ch == ' ' {\n",
    ),
    # 줄을 꺾은 뒤 다음 줄 머리의 빈칸 건너뛰기(운영 경로와 시험용 사본)
    ("renderer/composer/line_breaking.rs", LIVE + SKIP_OLD, LIVE + SKIP_NEW),
    ("renderer/composer/line_breaking.rs", MIRROR + SKIP_OLD, MIRROR + SKIP_NEW),
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
