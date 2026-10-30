    /// [claude-hwpx memo-rich-wasm] 메모 본문의 글자 모양 조각을 읽는다(메모 패널).
    #[wasm_bindgen(js_name = getMemoRich)]
    pub fn get_memo_rich_api(&self, field_id: u32) -> Result<String, JsValue> {
        self.get_memo_rich_json(field_id).map_err(|e| e.into())
    }

    /// [claude-hwpx memo-rich-wasm] 메모 본문을 글자 모양과 함께 바꾼다(메모 패널 「고치기」, cli memos format).
    #[wasm_bindgen(js_name = updateMemoRich)]
    pub fn update_memo_rich_api(&mut self, field_id: u32, json: &str) -> Result<String, JsValue> {
        self.update_memo_rich(field_id, json).map_err(|e| e.into())
    }

