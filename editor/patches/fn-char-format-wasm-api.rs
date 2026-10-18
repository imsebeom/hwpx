// ==== find ====
    /// 머리말/꼬리말 캐럿 위치의 글자 속성을 조회한다.
// ==== replace ====
    /// [claude-hwpx fn-char-format] 각주, 미주 글 범위에 글자 모양을 적용한다(칸 안 각주는 가짜 컨트롤 번호).
    #[wasm_bindgen(js_name = applyCharFormatInFootnote)]
    #[allow(clippy::too_many_arguments)]
    pub fn apply_char_format_in_footnote(
        &mut self,
        section_idx: u32,
        para_idx: u32,
        control_idx: u32,
        start_fn_para: u32,
        start_offset: u32,
        end_fn_para: u32,
        end_offset: u32,
        props_json: &str,
    ) -> Result<String, JsValue> {
        self.core
            .claude_apply_char_format_in_footnote_native(
                section_idx as usize,
                para_idx as usize,
                control_idx as usize,
                start_fn_para as usize,
                start_offset as usize,
                end_fn_para as usize,
                end_offset as usize,
                props_json,
            )
            .map_err(|e| e.into())
    }

    /// [claude-hwpx fn-char-format] 각주, 미주 글자 위치의 글자 모양을 조회한다.
    #[wasm_bindgen(js_name = getCharPropertiesInFootnote)]
    pub fn get_char_properties_in_footnote(
        &self,
        section_idx: u32,
        para_idx: u32,
        control_idx: u32,
        fn_para_idx: u32,
        char_offset: u32,
    ) -> Result<String, JsValue> {
        self.core
            .claude_get_char_properties_in_footnote_native(
                section_idx as usize,
                para_idx as usize,
                control_idx as usize,
                fn_para_idx as usize,
                char_offset as usize,
            )
            .map_err(|e| e.into())
    }

    /// 머리말/꼬리말 캐럿 위치의 글자 속성을 조회한다.
