"""개발용: 새 각주를 「각주」 스타일(보통 9pt)로 만들고, 표 칸 안에도 각주를 넣는다.

    python apply_fn_insert.py [--revert]

근거(2026-10-19 사용자 보고): 각주가 아직 없는 문서에 add_footnote 로 각주를 넣으면 커서 글자모양(본문 10pt)을 써서
한/글의 「각주」 스타일(9pt)과 달랐고, 문단 모양도 0번(바탕글)으로 고정돼 있었다. 또 엔진은 본문 문단에만 각주를 넣을 수
있어 칸 안 각주는 넣을 길이 없었다.

- 본문: 문서에 각주가 이미 있으면 그 모양을 따르고(종전과 같음), 없으면 「각주」 스타일(이름 또는 영문 Footnote)의
  글자모양과 문단 모양, 스타일 번호를 쓴다. 둘 다 없을 때만 커서 글자모양으로 떨어진다.
- 칸: claude_insert_footnote_in_cell_native(구역, 표를 담은 문단, 표 컨트롤, 칸, 칸 문단, 글자 위치). 같은 규칙으로 각주를
  만들어 칸 문단에 넣고 문서 전체 번호를 다시 매긴 뒤(note-renumber), 각주 문단은 fn-cell-target 가짜 번호로 다시 나누고 칸을
  다시 조판한다. wasm 이름은 insertFootnoteInCell, 돌려주는 noteControlIdx 는 각주 글 함수에 그대로 넘기는 가짜 번호다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx fn-insert]"

STYLE_LOOKUP_FIND = """        // 각주 내부 문단 생성: 기존 각주의 스타일을 참조하여 동일한 스타일 적용
        // 기존 각주가 없으면 본문 문단 스타일 사용
        let (default_char_shape_id, default_para_shape_id) = {
"""
STYLE_LOOKUP_REPL = f"""        // {TAG} 「각주」 스타일(이름 또는 영문 Footnote). 문서에 각주가 아직 없을 때 커서 글자모양(본문 10pt) 대신 쓴다.
        let claude_fn_style = self.claude_footnote_style();
        let mut claude_fn_found = false;
        // 각주 내부 문단 생성: 기존 각주의 스타일을 참조하여 동일한 스타일 적용
        // 기존 각주가 없으면 본문 문단 스타일 사용
        let (default_char_shape_id, default_para_shape_id) = {{
"""

FALLBACK_FIND = """            found.unwrap_or_else(|| {
                // 폴백 — 커서 offset 의 글자모양 기준 (첫 엔트리 아님).
"""
FALLBACK_REPL = """            // [claude-hwpx fn-insert] 기존 각주가 없으면 「각주」 스타일
            if found.is_none() {
                found = claude_fn_style.map(|st| (st.0, st.1));
            }
            claude_fn_found = found.is_some();
            found.unwrap_or_else(|| {
                // 폴백 — 커서 offset 의 글자모양 기준 (첫 엔트리 아님).
"""

INNER_FIND = """            para_shape_id: 0,
            style_id: 11, // 각주 style
"""
INNER_REPL = """            // [claude-hwpx fn-insert] 기존 각주나 「각주」 스타일을 찾았으면 그 문단 모양과 스타일 번호
            para_shape_id: if claude_fn_found { default_para_shape_id } else { 0 },
            style_id: claude_fn_style.map(|st| st.2).unwrap_or(11), // 각주 style
"""

CELL_FN = f"""    /// {TAG} 「각주」 스타일의 (글자모양, 문단 모양, 스타일 번호).
    pub(crate) fn claude_footnote_style(&self) -> Option<(u32, u16, u8)> {{
        self.document
            .doc_info
            .styles
            .iter()
            .enumerate()
            .find(|(_, st)| st.local_name == "각주" || st.english_name.eq_ignore_ascii_case("Footnote"))
            .map(|(i, st)| (st.char_shape_id as u32, st.para_shape_id, i.min(u8::MAX as usize) as u8))
    }}

    /// {TAG} 표 칸 문단의 글자 위치에 각주를 넣는다. 모양은 본문 각주와 같은 규칙(기존 각주, 「각주」 스타일, 커서 글자모양 순).
    /// 반환: `{{"ok":true,"cellParaIdx":N,"controlIdx":N,"noteControlIdx":N,"footnoteNumber":N}}`. noteControlIdx 는
    /// 각주 글 함수(getFootnoteInfo, insertTextInFootnote)에 표를 담은 문단 번호와 함께 넘기는 가짜 컨트롤 번호다.
    pub fn claude_insert_footnote_in_cell_native(
        &mut self,
        section_idx: usize,
        parent_para_idx: usize,
        control_idx: usize,
        cell_idx: usize,
        cell_para_idx: usize,
        char_offset: usize,
    ) -> Result<String, HwpError> {{
        use crate::model::footnote::Footnote;
        use crate::model::paragraph::{{CharShapeRef, LineSeg, Paragraph}};

        fn first_note(paras: &[Paragraph], depth: usize) -> Option<(u32, u16)> {{
            if depth > 8 {{
                return None;
            }}
            for p in paras {{
                for c in &p.controls {{
                    match c {{
                        Control::Footnote(f) => {{
                            if let Some(fp) = f.paragraphs.first() {{
                                return Some((fp.char_shapes.first().map(|cs| cs.char_shape_id).unwrap_or(0), fp.para_shape_id));
                            }}
                        }}
                        Control::Table(t) => {{
                            for cell in &t.cells {{
                                if let Some(r) = first_note(&cell.paragraphs, depth + 1) {{
                                    return Some(r);
                                }}
                            }}
                        }}
                        _ => {{}}
                    }}
                }}
            }}
            None
        }}

        let err = |m: &str| HwpError::RenderError(m.to_string());
        let style = self.claude_footnote_style();
        let (char_shape_id, para_shape_id) = {{
            let section = self.document.sections.get(section_idx).ok_or_else(|| err("구역 번호 범위 초과"))?;
            let host = section.paragraphs.get(parent_para_idx).ok_or_else(|| err("문단 번호 범위 초과"))?;
            let cell_para = match host.controls.get(control_idx) {{
                Some(Control::Table(t)) => t
                    .cells
                    .get(cell_idx)
                    .ok_or_else(|| err("칸 번호 범위 초과"))?
                    .paragraphs
                    .get(cell_para_idx)
                    .ok_or_else(|| err("칸 문단 번호 범위 초과"))?,
                _ => return Err(err("표 컨트롤이 아닙니다")),
            }};
            first_note(&section.paragraphs, 0)
                .or_else(|| style.map(|st| (st.0, st.1)))
                .unwrap_or((cell_para.char_shape_id_at(char_offset).unwrap_or(0), 0))
        }};

        // 본문 각주와 같은 한컴 contract(빈칸 둘 사이에 AutoNumber)
        let auto_num = crate::model::control::AutoNumber {{
            number_type: crate::model::control::AutoNumberType::Footnote,
            format: 0,
            superscript: false,
            number: 1,
            assigned_number: 1,
            user_symbol: '\\0',
            prefix_char: '\\0',
            suffix_char: ')',
        }};
        let inner_para = Paragraph {{
            text: "  ".to_string(),
            char_count: 10,
            char_count_msb: true,
            control_mask: 1u32 << 0x12,
            char_offsets: vec![0, 8],
            para_shape_id,
            style_id: style.map(|st| st.2).unwrap_or(11),
            char_shapes: vec![CharShapeRef {{
                start_pos: 0,
                char_shape_id,
            }}],
            controls: vec![Control::AutoNumber(auto_num)],
            line_segs: vec![LineSeg {{
                text_start: 0,
                line_height: 1000,
                text_height: 1000,
                baseline_distance: 850,
                line_spacing: 600,
                segment_width: 0,
                tag: LineSeg::TAG_SINGLE_SEGMENT_LINE,
                ..Default::default()
            }}],
            has_para_text: true,
            ..Default::default()
        }};
        let footnote = Footnote {{
            number: 1,
            paragraphs: vec![inner_para],
            after_decoration_letter: 0x0029,
            ..Default::default()
        }};

        self.document.sections[section_idx].raw_stream = None;
        let insert_idx = {{
            let Some(Control::Table(table)) =
                self.document.sections[section_idx].paragraphs[parent_para_idx].controls.get_mut(control_idx)
            else {{
                return Err(err("표 컨트롤이 아닙니다"));
            }};
            let paragraph = &mut table.cells[cell_idx].paragraphs[cell_para_idx];
            let positions = crate::document_core::helpers::find_control_text_positions(paragraph);
            let idx = positions.iter().position(|&pos| pos > char_offset).unwrap_or(paragraph.controls.len());
            paragraph.align_ctrl_data_records();
            paragraph.controls.insert(idx, Control::Footnote(Box::new(footnote)));
            paragraph.ctrl_data_records.insert(idx, None);
            paragraph.shift_for_inline_control_insert(char_offset);
            paragraph.char_count += 8;
            paragraph.control_mask |= 1u32 << 0x0011;
            paragraph.has_para_text = true;
            idx
        }};

        self.claude_renumber_notes();
        let note_idx = self.claude_register_fn_cell(parent_para_idx, control_idx, cell_idx, cell_para_idx, insert_idx);
        let number = match self.claude_note_number(section_idx, parent_para_idx, note_idx) {{
            Some(n) => n,
            None => 1,
        }};

        self.reflow_footnote_paragraph(section_idx, parent_para_idx, note_idx, 0);
        self.mark_cell_control_dirty(section_idx, parent_para_idx, control_idx);
        self.reflow_cell_paragraph(section_idx, parent_para_idx, control_idx, cell_idx, cell_para_idx);
        self.recalculate_cell_paragraph_vpos_native(section_idx, parent_para_idx, control_idx, cell_idx, cell_para_idx, None);
        self.sync_tac_table_host_line(section_idx, parent_para_idx, control_idx);
        self.mark_section_dirty(section_idx);
        self.paginate_if_needed();
        self.invalidate_page_tree_cache();

        Ok(format!(
            "{{{{\\"ok\\":true,\\"cellParaIdx\\":{{}},\\"controlIdx\\":{{}},\\"noteControlIdx\\":{{}},\\"footnoteNumber\\":{{}}}}}}",
            cell_para_idx, insert_idx, note_idx, number
        ))
    }}

    /// {TAG} 각주 번호(가짜 컨트롤 번호도 받는다). 각주 안 AutoNumber 도 같은 번호로 맞춘다.
    fn claude_note_number(&mut self, section_idx: usize, para_idx: usize, control_idx: usize) -> Option<u16> {{
        let cells = self.claude_fn_cells.clone();
        let ctrl = crate::document_core::commands::footnote_ops::claude_note_ctrl_mut(
            &mut self.document,
            &cells,
            section_idx,
            para_idx,
            control_idx,
        )?;
        let Control::Footnote(f) = ctrl else {{
            return None;
        }};
        let n = f.number;
        for p in f.paragraphs.iter_mut() {{
            for c in p.controls.iter_mut() {{
                if let Control::AutoNumber(a) = c {{
                    a.number = n;
                    a.assigned_number = n;
                }}
            }}
        }}
        Some(n)
    }}

    /// 미주를 삽입한다.
"""

WASM_FIND = """    /// 미주를 삽입한다.
    #[wasm_bindgen(js_name = insertEndnote)]
"""
WASM_REPL = f"""    /// {TAG} 표 칸 문단에 각주를 넣는다. 돌려주는 noteControlIdx 를 각주 글 함수의 컨트롤 번호로 쓴다.
    #[wasm_bindgen(js_name = insertFootnoteInCell)]
    pub fn insert_footnote_in_cell(
        &mut self,
        section_idx: u32,
        parent_para_idx: u32,
        control_idx: u32,
        cell_idx: u32,
        cell_para_idx: u32,
        char_offset: u32,
    ) -> Result<String, JsValue> {{
        self.core
            .claude_insert_footnote_in_cell_native(
                section_idx as usize,
                parent_para_idx as usize,
                control_idx as usize,
                cell_idx as usize,
                cell_para_idx as usize,
                char_offset as usize,
            )
            .map_err(|e| e.into())
    }}

    /// 미주를 삽입한다.
    #[wasm_bindgen(js_name = insertEndnote)]
"""

TEST_FIND = """    fn insert_footnote_fallback_inherits_char_shape_at_cursor_offset() {
        a_footnote_host_paragraph_is_reflowed_on_its_column_not_the_page();
        let mut core = core_with_mixed_shape_paragraph();
"""
TEST_REPL = """    fn insert_footnote_fallback_inherits_char_shape_at_cursor_offset() {
        a_footnote_host_paragraph_is_reflowed_on_its_column_not_the_page();
        let mut core = core_with_mixed_shape_paragraph();
        // [claude-hwpx fn-insert] 「각주」 스타일이 있으면 그쪽이 먼저라 마지막 폴백을 보려고 지운다
        for st in core.document.doc_info.styles.iter_mut() {
            if st.local_name == "각주" || st.english_name.eq_ignore_ascii_case("Footnote") {
                st.local_name = String::new();
                st.english_name = String::new();
            }
        }
"""

EDITS = [
    ("document_core/commands/object_ops/note.rs", STYLE_LOOKUP_FIND, STYLE_LOOKUP_REPL),
    ("document_core/commands/object_ops/note.rs", FALLBACK_FIND, FALLBACK_REPL),
    ("document_core/commands/object_ops/note.rs", INNER_FIND, INNER_REPL),
    (
        "document_core/commands/object_ops/note.rs",
        "    /// 미주를 삽입한다.\n",
        CELL_FN,
    ),
    ("document_core/commands/object_ops/note.rs", TEST_FIND, TEST_REPL),
    ("wasm_api.rs", WASM_FIND, WASM_REPL),
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
