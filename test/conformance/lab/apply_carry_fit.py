"""개발용(이미 소스에 들어간 수정을 패치로 내보내는 목록): 정답본 쪽수가 하나 많던 d007, d021, d165, d331.

    python export_patches.py apply_carry_fit carry-fit

- tac-note-stored: 칸 각주가 든 글자처럼 취급 표의 저장 줄이 이 쪽을 가리키면 각주 몫을 빼지 않고 맞춘다(d021: 표 5쪽, 각주 6쪽).
- carry-empty-page: 각주를 넘긴 뒤 다음 문단의 저장 위치가 0 이면 그 문단이 쪽을 넘기므로 여기서 또 넘기지 않는다(각주만 든 쪽이 생겨 1쪽 늘었다).
- stale-line-height: 표 문단 글 줄의 저장 높이가 표 높이로 적혀 있어도 한/글은 다음 줄 위치까지만 나아간다(d007, d165: 7176, 위치 차이 1760).
"""

TAG = "[claude-hwpx tac-note-stored]"
TAG2 = "[claude-hwpx carry-empty-page]"
TAG3 = "[claude-hwpx stale-line-height]"
TS = "renderer/typeset.rs"
LB = "renderer/composer/line_breaking.rs"

EDITS = [
    (
        TS,
        (
            "                    saved_table_bounds_fit_at_flow_tail(\n"
            "                        bounds,\n"
            "                        st.current_height,\n"
            "                        available,\n"
            "                        saved_tac_table_frame_height,\n"
            "                    )\n"
            "                });\n"
            "        // [#3837] 저장 vpos 되돌아감은"
        ),
        (
            "                    saved_table_bounds_fit_at_flow_tail(\n"
            "                        bounds,\n"
            "                        st.current_height,\n"
            f"                        // {TAG} 저장 줄이 이 쪽에 표를 두면 각주 몫을 빼지 않고 맞춘다. 각주만 다음 쪽으로 간다(d021, 표 5쪽, 각주 6쪽)\n"
            "                        st.available_height(),\n"
            "                        saved_tac_table_frame_height,\n"
            "                    )\n"
            "                });\n"
            "        // [#3837] 저장 vpos 되돌아감은"
        ),
    ),
    (
        TS,
        "    claude_carry_notes: Vec<(crate::renderer::pagination::FootnoteRef, f64)>,\n",
        (
            "    claude_carry_notes: Vec<(crate::renderer::pagination::FootnoteRef, f64)>,\n"
            f"    /// {TAG2} 다음 문단 첫 줄의 저장 위치\n"
            "    claude_next_first_vpos: Option<i32>,\n"
        ),
    ),
    (
        TS,
        "            claude_carry_notes: Vec::new(),\n",
        "            claude_carry_notes: Vec::new(),\n            claude_next_first_vpos: None,\n",
    ),
    (
        TS,
        "                    if st.profile.hwpx_container() && !st.claude_carry_notes.is_empty() {\n                        st.advance_column_or_new_page();\n                    }\n",
        (
            f"                    // {TAG2} 다음 문단의 저장 위치가 0 이면 그 문단이 쪽을 넘긴다. 여기서도 넘기면 각주만 든 쪽이 생긴다(d021, d331)\n"
            "                    if st.profile.hwpx_container()\n"
            "                        && !st.claude_carry_notes.is_empty()\n"
            "                        && st.claude_next_first_vpos != Some(0)\n"
            "                    {\n"
            "                        st.advance_column_or_new_page();\n"
            "                    }\n"
        ),
    ),
    (
        TS,
        "                self.typeset_table_paragraph(\n                    &mut st,\n",
        (
            "                st.claude_next_first_vpos = paragraphs.get(para_idx + 1).and_then(|n| n.line_segs.first()).map(|s| s.vertical_pos);\n"
            "                self.typeset_table_paragraph(\n"
            "                    &mut st,\n"
        ),
    ),
    (
        LB,
        "        let last = para.line_segs.last().unwrap();\n        prev = Some((last.vertical_pos + last.line_height + last.line_spacing, after, is_float));\n",
        (
            f"        // {TAG3} 표 문단 글 줄의 저장 높이가 표 높이로 적혀 있어도(d007: 7176, 다음 줄과 1760 차이) 한/글은 줄 위치 차이만큼만 나아간다\n"
            "        if para.controls.iter().any(|c| matches!(c, Control::Table(t) if t.common.treat_as_char)) {\n"
            "            for i in 1..para.line_segs.len() {\n"
            "                let (cur, next) = (para.line_segs[i - 1].clone(), para.line_segs[i].vertical_pos);\n"
            "                let diff = next - cur.vertical_pos;\n"
            "                if diff > 0 && cur.line_height + cur.line_spacing > diff + 2 {\n"
            "                    para.line_segs[i - 1].line_height = (diff - cur.line_spacing).max(cur.text_height.min(diff));\n"
            "                }\n"
            "            }\n"
            "        }\n"
            "        let last = para.line_segs.last().unwrap();\n"
            "        prev = Some((last.vertical_pos + last.line_height + last.line_spacing, after, is_float));\n"
        ),
    ),
]
