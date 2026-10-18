// ==== find ====
    /// 미주를 삽입한다.
    #[wasm_bindgen(js_name = insertEndnote)]
// ==== replace ====
    /// [claude-hwpx fn-insert] 표 칸 문단에 각주를 넣는다. 돌려주는 noteControlIdx 를 각주 글 함수의 컨트롤 번호로 쓴다.
    #[wasm_bindgen(js_name = insertFootnoteInCell)]
    pub fn insert_footnote_in_cell(
        &mut self,
        section_idx: u32,
        parent_para_idx: u32,
        control_idx: u32,
        cell_idx: u32,
        cell_para_idx: u32,
        char_offset: u32,
    ) -> Result<String, JsValue> {
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
    }

    /// 미주를 삽입한다.
    #[wasm_bindgen(js_name = insertEndnote)]
