// ==== find ====
    /// 글로벌 쪽 번호에 해당하는 첫 문단 위치 반환
    #[wasm_bindgen(js_name = getPositionOfPage)]
// ==== replace ====
    /// [claude-hwpx footnote-search] 각주, 미주 안 매치 목록(JSON 배열)
    #[wasm_bindgen(js_name = searchNoteText)]
    pub fn search_note_text(&self, query: &str, case_sensitive: bool) -> String {
        self.core.claude_search_note_text_native(query, case_sensitive)
    }

    /// [claude-hwpx footnote-search] 각주, 미주 안 index 번째 매치 하나를 바꾼다
    #[wasm_bindgen(js_name = replaceNoteHit)]
    pub fn replace_note_hit(
        &mut self,
        query: &str,
        new_text: &str,
        case_sensitive: bool,
        index: u32,
    ) -> Result<String, JsValue> {
        self.core
            .claude_replace_note_hit_native(query, new_text, case_sensitive, index as usize)
            .map_err(|e| e.into())
    }

    /// 글로벌 쪽 번호에 해당하는 첫 문단 위치 반환
    #[wasm_bindgen(js_name = getPositionOfPage)]
