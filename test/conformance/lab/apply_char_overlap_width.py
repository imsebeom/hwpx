"""개발용: 동그라미 글자 겹치기(hp:compose circleType=SHAPE_CIRCLE)도 줄 나눔에서 「◯」 글자 폭만큼 차지한다.

    python apply_char_overlap_width.py [--revert]

근거(2026-10-18 블랙박스 실측): d113 을 한/글 2024 로 PDF 로 뽑으니 칸 문단 첫머리 겹친 글자(동그라미 안 「유」, charSz -3)는
「◯」 글리프(x 456.6)와 작은 「유」로 그려지고 다음 빈칸이 x 465.84 에 왔다. 폭 9.24pt = 10pt x 장평 0.95 x 함초롬바탕 ◯ 폭 0.97em
(9.215pt). 자간(-5%)은 들어가지 않는다. 엔진은 겹친 글자를 확장 조판 부호(폭 0)로만 세어 줄을 1~2자 늦게 꺾었다
(정답본 불일치 18곳: d113, d127, d144, d073, d334). 근거가 동그라미뿐이라 테두리 1(원)만 바꾼다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx char-overlap-width]"
F = "renderer/composer/line_breaking.rs"

EDITS = [
    (
        F,
        "fn flow_inline_controls(para: &Paragraph) -> Vec<FlowInlineControl> {\n"
        "    let text_len = para.text.chars().count();\n"
        "    para.controls\n"
        "        .iter()\n"
        "        .zip(para.control_text_positions())\n"
        "        .filter_map(|(control, char_position)| {\n",
        "fn flow_inline_controls(para: &Paragraph, styles: &ResolvedStyleSet) -> Vec<FlowInlineControl> {\n"
        "    let text_len = para.text.chars().count();\n"
        "    para.controls\n"
        "        .iter()\n"
        "        .zip(para.control_text_positions())\n"
        "        .filter_map(|(control, char_position)| {\n"
        f"            // {TAG} 동그라미 겹친 글자는 그 자리 글자 모양의 「◯」 폭(장평 반영, 자간 빼고)만큼 차지한다(d113 한/글 PDF 실측)\n"
        "            if let Control::CharOverlap(overlap) = control {\n"
        "                if overlap.border_type != 1 || char_position >= text_len {\n"
        "                    return None;\n"
        "                }\n"
        "                let utf16 = para.char_offsets.get(char_position).copied().unwrap_or(char_position as u32);\n"
        "                let style_id = super::find_active_char_shape(&para.char_shapes, utf16);\n"
        "                let mut ts = crate::renderer::layout::resolved_to_text_style(\n"
        "                    styles,\n"
        "                    style_id,\n"
        "                    crate::renderer::style_resolver::detect_lang_category('\\u{25EF}'),\n"
        "                );\n"
        "                ts.letter_spacing = 0.0;\n"
        '                let width_hwp = (estimate_text_width_unrounded("\\u{25EF}", &ts) * 75.0).round() as i32;\n'
        "                return Some(FlowInlineControl { char_position, width_hwp, height_hwp: 0, baseline_distance_hwp: None });\n"
        "            }\n",
    ),
    (
        F,
        "    let text_chars = para.text.chars().collect::<Vec<_>>();\n"
        "    let inline_controls = flow_inline_controls(para);\n",
        "    let text_chars = para.text.chars().collect::<Vec<_>>();\n"
        "    let inline_controls = flow_inline_controls(para, styles); // [claude-hwpx char-overlap-width]\n",
    ),
    (
        F,
        "    // inline token: it is represented by the caller's exclusion instead.\n"
        "    let inline_controls = flow_inline_controls(para);\n",
        "    // inline token: it is represented by the caller's exclusion instead.\n"
        "    let inline_controls = flow_inline_controls(para, styles); // [claude-hwpx char-overlap-width]\n",
    ),
    (
        F,
        "    let text_len = text_chars.len();\n"
        "    let inline_controls = flow_inline_controls(para);\n",
        "    let text_len = text_chars.len();\n"
        "    let inline_controls = flow_inline_controls(para, styles); // [claude-hwpx char-overlap-width]\n",
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
