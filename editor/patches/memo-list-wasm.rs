// ==== find ====
    /// 문서 내 모든 필드 목록을 JSON 배열로 반환한다.
// ==== replace ====
    /// [claude-hwpx memo-list-wasm] 메모 목록. 메모마다 번호, 작성자, 작성 일시, 본문, 걸린 글과 그 범위(캐럿 축).
    /// `getFieldList` 와 달리 걸린 글이 문단을 넘는 메모도 든다.
    #[wasm_bindgen(js_name = getMemoList)]
    pub fn get_memo_list(&self) -> String {
        self.get_memo_list_json()
    }

    /// 문서 내 모든 필드 목록을 JSON 배열로 반환한다.
