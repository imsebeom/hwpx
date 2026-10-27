    /// [claude-hwpx memo-crud-wasm] 메모를 지운다(메모 패널 「지우기」, cli memos del). 걸린 글은 남는다.
    /// field_id 는 getMemoList 의 fieldId.
    #[wasm_bindgen(js_name = deleteMemo)]
    pub fn delete_memo_api(&mut self, field_id: u32) -> Result<String, JsValue> {
        self.delete_memo(field_id).map_err(|e| e.into())
    }

    /// [claude-hwpx memo-crud-wasm] 메모 본문을 바꾼다(메모 패널 「고치기」, cli memos edit). 줄바꿈마다 문단 하나.
    #[wasm_bindgen(js_name = updateMemoBody)]
    pub fn update_memo_body_api(&mut self, field_id: u32, body: &str) -> Result<String, JsValue> {
        self.update_memo_body(field_id, body).map_err(|e| e.into())
    }

