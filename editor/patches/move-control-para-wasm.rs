    /// [claude-hwpx move-control-para] 본문 개체를 문단 목록의 dst 자리로 옮긴다(끌어 옮기기를 놓을 때).
    /// 반환: JSON `{"ok":true,"ppi":<새 문단>,"ci":<새 컨트롤>,"moved":<bool>}`
    #[wasm_bindgen(js_name = moveControlToParagraph)]
    pub fn move_control_to_paragraph(
        &mut self,
        section_idx: u32,
        para_idx: u32,
        control_idx: u32,
        dst: u32,
    ) -> Result<String, JsValue> {
        self.claude_move_control_to_para(
            section_idx as usize,
            para_idx as usize,
            control_idx as usize,
            dst as usize,
        )
        .map_err(|e| e.into())
    }

