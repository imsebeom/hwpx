"""개발용: 번호 문단(heading NUMBER)의 번호 자리를 줄 나눔에서 뺀다.

    python apply_number_head.py [--revert]

근거(lab e29, 20pt, 함초롬바탕과 맑은 고딕): 한/글 2024 는 번호 뒤 본문을 「번호 글의 실제 폭 + 본문과의 거리」에서 시작한다.
거리는 PERCENT 면 글자 크기 x %, HWPUNIT 이면 그 값이고, 너비 보정값을 더한다. 「1.」 폭이 함초롬바탕 17.4pt, 맑은 고딕 15.4pt 로
글꼴마다 달라 글머리표(전각이면 1em 고정)와 다르다. 자동 내어쓰기가 켜져 있으면 이어지는 줄도 같은 자리에서 시작하고,
꺼져 있으면 첫 줄만 좁다(이어지는 줄은 문단 왼쪽 여백과 들여쓰기 그대로). 종전 엔진은 번호를 줄 나눔에서 빼지 않아 한 줄에
두세 글자를 더 담았다(불일치 중 번호 문단 첫 줄 13건, 줄 수 6건).
번호 값은 줄 나눔 단계에 계수기가 없어 시작 번호로 잰다(「2.」 와 「1.」 은 폭이 같고, 두 자리가 되는 문단만 다르다).
「번호 너비를 실제 폭에 맞춤」을 끈 정의(useInstWidth=0)는 아직 규칙을 모르므로 다루지 않는다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx number-head]"
LB = "renderer/composer/line_breaking.rs"

NEW_FN = r"""
/// [claude-hwpx number-head] 번호 문단 머리 정의의 원본 태그(raw_para_heads 에서 그 수준의 `<hh:paraHead ...>`).
fn claude_raw_para_head(raw: &str, level: usize) -> Option<&str> {
    let key = format!(" level=\"{}\"", level);
    let mut rest = raw;
    while let Some(i) = rest.find("paraHead ") {
        let tail = &rest[i..];
        let end = tail.find('>')?;
        if tail[..end].contains(&key) {
            return Some(&tail[..end]);
        }
        rest = &tail[end..];
    }
    None
}

/// [claude-hwpx number-head] 번호 문단에서 한/글이 번호에 내주는 자리(HWPUNIT)와 자동 내어쓰기 여부.
///
/// 한/글 2024 실측(test/conformance/lab e29): 자리 = 번호 글의 실제 폭 + 본문과의 거리(PERCENT 면 글자 크기 x %,
/// HWPUNIT 이면 그 값) + 너비 보정값. 번호 값은 시작 번호로 잰다(계수기는 그리는 단계에만 있다).
fn claude_number_head_hwp(para: &Paragraph, styles: &ResolvedStyleSet) -> Option<(i32, bool)> {
    let para_style = styles.para_styles.get(para.para_shape_id as usize)?;
    if para_style.head_type != crate::model::style::HeadType::Number {
        return None;
    }
    let numbering = styles
        .numberings
        .get((para_style.numbering_id as usize).checked_sub(1)?)?;
    let level = (para_style.para_level as usize).min(6);
    let format = &numbering.level_formats[level];
    if format.is_empty() {
        return None;
    }
    let head = numbering.heads[level];
    let (auto_indent, percent, inst_width) =
        match numbering.raw_para_heads.as_deref().and_then(|raw| claude_raw_para_head(raw, level + 1)) {
            Some(tag) => (
                !tag.contains("autoIndent=\"0\""),
                !tag.contains("textOffsetType=\"HWPUNIT\""),
                !tag.contains("useInstWidth=\"0\""),
            ),
            None => (head.attr & 0x08 != 0, head.attr & 0x10 == 0, head.attr & 0x04 != 0),
        };
    if !inst_width {
        return None;
    }
    let text = crate::renderer::layout::expand_numbering_format(
        format,
        &[1; 7],
        numbering,
        &numbering.level_start_numbers,
        level,
    );
    if text.is_empty() {
        return None;
    }
    let char_style_id = if (head.char_shape_id as usize) < styles.char_styles.len() {
        head.char_shape_id
    } else {
        para.char_shapes.first().map(|shape| shape.char_shape_id)?
    };
    let font_size = styles
        .char_styles
        .get(char_style_id as usize)
        .map(|style| style.font_size)
        .filter(|size| *size > 0.0)?;
    let width_px: f64 = text
        .chars()
        .map(|ch| {
            let ts = resolved_to_text_style(styles, char_style_id, detect_lang_category(ch));
            estimate_text_width_unrounded(&ch.to_string(), &ts)
        })
        .sum();
    // 1/1800 인치(HWPUNIT/4) 단위
    let quarter = 75.0 / 4.0;
    let advance = if percent {
        ((width_px + font_size * f64::from(head.text_distance) / 100.0) * quarter + 0.5 + 1e-6).floor() as i32 * 4
    } else {
        (width_px * quarter + 0.5 + 1e-6).floor() as i32 * 4 + i32::from(head.text_distance)
    };
    Some((advance + i32::from(head.width_adjust), auto_indent))
}
"""

EDITS = [
    (
        LB,
        "    Some(advance + i32::from(bullet.width_adjust))\n}\n\nfn reflow_line_segs_impl(",
        "    Some(advance + i32::from(bullet.width_adjust))\n}\n"
        + NEW_FN
        + "\nfn reflow_line_segs_impl(",
    ),
    (
        LB,
        "        .filter(|advance| *advance > 0 && *advance < seg_width_hwp)\n        .unwrap_or(0);\n    let fill_box = if bullet_advance_hwp > 0 {\n",
        "        .filter(|advance| *advance > 0 && *advance < seg_width_hwp)\n        .unwrap_or(0);\n"
        f"    // {TAG} 번호 자리도 뺀다. 자동 내어쓰기면 글머리표처럼 모든 줄을 좁히고, 아니면 첫 줄만 좁히도록 들여쓰기를 고친다\n"
        "    // (상자를 m 만큼 좁히고 들여쓰기로 나머지를 맞춘다: 첫 줄 = 폭 - max(들여쓰기, 0) - 자리, 이어지는 줄 = 폭 - max(-들여쓰기, 0))\n"
        "    let mut claude_indent_override: Option<f64> = None;\n"
        "    let bullet_advance_hwp = if bullet_advance_hwp > 0 {\n"
        "        bullet_advance_hwp\n"
        "    } else {\n"
        "        match claude_number_head_hwp(para, styles).filter(|(advance, _)| *advance > 0 && *advance < seg_width_hwp) {\n"
        "            Some((advance, true)) => advance,\n"
        "            Some((advance, false)) => {\n"
        "                let indent = styles.para_styles.get(para.para_shape_id as usize).map(|s| s.indent).unwrap_or(0.0);\n"
        "                let advance_px = crate::renderer::hwpunit_to_px(advance, dpi);\n"
        "                let shift_px = if indent >= 0.0 { 0.0 } else { advance_px.min(-indent) };\n"
        "                claude_indent_override = Some(if indent >= 0.0 {\n"
        "                    indent + advance_px\n"
        "                } else if advance_px >= -indent {\n"
        "                    advance_px + indent\n"
        "                } else {\n"
        "                    indent + advance_px\n"
        "                });\n"
        "                px_to_hwpunit(shift_px, dpi)\n"
        "            }\n"
        "            None => 0,\n"
        "        }\n"
        "    };\n"
        "    let fill_box = if bullet_advance_hwp > 0 {\n",
    ),
    (
        LB,
        "    let indent_px = para_style.map(|s| s.indent).unwrap_or(0.0);\n",
        f"    // {TAG} 번호 자리가 첫 줄만 좁히면 고친 들여쓰기\n"
        "    let indent_px = claude_indent_override.unwrap_or_else(|| para_style.map(|s| s.indent).unwrap_or(0.0));\n",
    ),
    (
        LB,
        "        if let Some(mut projected) = layout_paragraph_in_frame(para, &mut frame, styles, dpi) {\n",
        "        if let Some(mut projected) =\n"
        f"            // {TAG}\n"
        "            layout_paragraph_in_frame_indent(para, &mut frame, styles, dpi, claude_indent_override)\n"
        "        {\n",
    ),
    (
        LB,
        "    layout_paragraph_in_frame_impl(para, frame, styles, dpi, true)\n}\n\nfn layout_paragraph_in_frame_impl(\n    para: &Paragraph,\n    frame: &mut LayoutFrame,\n    styles: &ResolvedStyleSet,\n    dpi: f64,\n    allow_kerning: bool,\n) -> Option<Vec<LineSeg>> {\n",
        "    layout_paragraph_in_frame_impl(para, frame, styles, dpi, true, None)\n}\n\n"
        f"/// {TAG} 들여쓰기를 문단 모양 대신 주어진 값으로 쓰는 판(번호 자리가 첫 줄만 좁힐 때).\n"
        "fn layout_paragraph_in_frame_indent(\n    para: &Paragraph,\n    frame: &mut LayoutFrame,\n    styles: &ResolvedStyleSet,\n    dpi: f64,\n    indent_override: Option<f64>,\n) -> Option<Vec<LineSeg>> {\n"
        "    layout_paragraph_in_frame_impl(para, frame, styles, dpi, true, indent_override)\n}\n\n"
        "fn layout_paragraph_in_frame_impl(\n    para: &Paragraph,\n    frame: &mut LayoutFrame,\n    styles: &ResolvedStyleSet,\n    dpi: f64,\n    allow_kerning: bool,\n    indent_override: Option<f64>,\n) -> Option<Vec<LineSeg>> {\n",
    ),
    (
        LB,
        "    let indent_px = para_style.map(|style| style.indent).unwrap_or(0.0);\n",
        "    let indent_px = indent_override.unwrap_or_else(|| para_style.map(|style| style.indent).unwrap_or(0.0));\n",
    ),
    (
        LB,
        "        return layout_paragraph_in_frame_impl(para, frame, styles, dpi, false);\n",
        "        return layout_paragraph_in_frame_impl(para, frame, styles, dpi, false, indent_override);\n",
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
