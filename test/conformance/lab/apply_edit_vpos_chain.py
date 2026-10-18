"""개발용: 편집 경로가 구역 본문을 다시 접은 뒤에도 문서를 열 때처럼 vpos 사슬(문단 간격, 위아래 배치 개체 높이)을 잇는다.

    python apply_edit_vpos_chain.py [--revert]

근거: editor/tests/edit_consistency.mjs — page_setup(여백) 뒤 「편집 직후 조판」은 10쪽, 같은 결과를 처음부터 조판하면 9쪽.
reflow_body_paragraphs_in_section 은 모든 본문 문단의 줄을 지우고 다시 만들지만 vpos 를 문단마다 0 으로 두었다.
열기 경로는 같은 경우에 vpos 사슬을 잇는다(document.rs running_vpos, synth-vpos-spacing).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx edit-vpos-chain]"

CHAIN_FN = (
    f"/// {TAG} 줄을 모두 새로 만든 본문 문단들의 vpos 사슬을 문서 열기 경로(document.rs running_vpos, synth-vpos-spacing)처럼 잇는다:\n"
    "/// 문단 사이 = 앞 문단 아래 간격 + 이 문단 위 간격(표만 담은 문단의 아래 간격은 뺀다), 위아래 배치 그림과 표는 줄 높이보다 크면\n"
    "/// 그만큼 더한다. 줄이 없는 문단은 건너뛰고 아래 간격도 넘기지 않는다.\n"
    "fn claude_rechain_vpos(paragraphs: &mut [crate::model::paragraph::Paragraph], styles: &ResolvedStyleSet, dpi: f64) {\n"
    "    use crate::model::control::Control;\n"
    "    use crate::model::shape::TextWrap;\n"
    "    let hu = |px: f64| (px * 7200.0 / dpi).round() as i32;\n"
    "    let mut running: i32 = 0;\n"
    "    let mut prev_after: i32 = 0;\n"
    "    for para in paragraphs.iter_mut() {\n"
    "        if para.line_segs.is_empty() {\n"
    "            prev_after = 0;\n"
    "            continue;\n"
    "        }\n"
    "        let style = styles.para_styles.get(para.para_shape_id as usize);\n"
    "        running += prev_after + hu(style.map(|s| s.spacing_before).unwrap_or(0.0));\n"
    "        let mut v = running;\n"
    "        for seg in para.line_segs.iter_mut() {\n"
    "            seg.vertical_pos = v;\n"
    "            let h = if seg.line_height > seg.text_height && seg.text_height > 0 { seg.text_height } else { seg.line_height };\n"
    "            v += h + seg.line_spacing;\n"
    "        }\n"
    "        let seg_total: i32 = para.line_segs.iter().map(|s| s.line_height + s.line_spacing).sum();\n"
    "        for ctrl in para.controls.iter() {\n"
    "            let obj = match ctrl {\n"
    "                Control::Picture(p)\n"
    "                    if !p.common.treat_as_char && matches!(p.common.text_wrap, TextWrap::TopAndBottom) && p.common.height > 0 =>\n"
    "                {\n"
    "                    p.common.height as i32 + p.common.vertical_offset as i32\n"
    "                }\n"
    "                Control::Table(t)\n"
    "                    if !t.common.treat_as_char && matches!(t.common.text_wrap, TextWrap::TopAndBottom) && t.common.height > 0 && t.raw_ctrl_data.is_empty() =>\n"
    "                {\n"
    "                    t.common.height as i32 + t.common.vertical_offset as i32 + t.outer_margin_top as i32 + t.outer_margin_bottom as i32\n"
    "                }\n"
    "                _ => continue,\n"
    "            };\n"
    "            if obj > seg_total {\n"
    "                v += obj - seg_total;\n"
    "            }\n"
    "        }\n"
    "        running = v;\n"
    "        let table_only = para.text.trim().is_empty()\n"
    "            && para.controls.iter().any(|c| {\n"
    "                matches!(c, Control::Table(t) if !t.common.treat_as_char && matches!(t.common.text_wrap, TextWrap::TopAndBottom))\n"
    "            });\n"
    "        prev_after = if table_only { 0 } else { hu(style.map(|s| s.spacing_after).unwrap_or(0.0)) };\n"
    "    }\n"
    "}\n\n"
)

EDITS = [
    (
        "document_core/commands/formatting.rs",
        "fn body_paragraph_box_for_para_shape(\n",
        CHAIN_FN + "fn body_paragraph_box_for_para_shape(\n",
    ),
    (
        "document_core/commands/formatting.rs",
        "            para.line_segs.clear();\n            reflow_line_segs(para, paragraph_box, &styles, dpi);\n        }\n    }\n",
        "            para.line_segs.clear();\n            reflow_line_segs(para, paragraph_box, &styles, dpi);\n        }\n"
        f"        // {TAG} 줄을 모두 새로 만들었으니 문서 열기처럼 vpos 사슬을 잇는다(종전에는 문단마다 0)\n"
        "        claude_rechain_vpos(&mut section.paragraphs, &styles, dpi);\n"
        "    }\n",
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
