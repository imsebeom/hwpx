    /// [claude-hwpx caret-axis] 캐럿 축 위치를 다른 축으로(또는 그 반대로)바꾼다.
    /// `path_json` 이 빈 문자열이면 본문 문단 `para_idx`, 아니면 `para_idx` 를 부모 문단으로 한 셀 경로.
    /// mode: 0 캐럿→글자, 1 글자→캐럿, 2 캐럿→나누기, 3 나누기→캐럿, 4 캐럿이 인라인 개체 바로 뒤인가(0/1),
    /// 5 문단의 캐럿 축 길이(offset 무시).
    #[wasm_bindgen(js_name = convertCaretOffset)]
    pub fn convert_caret_offset(
        &self,
        section_idx: u32,
        para_idx: u32,
        path_json: &str,
        offset: u32,
        mode: u32,
    ) -> Result<u32, JsValue> {
        use crate::document_core::helpers as axis;
        let sec = section_idx as usize;
        let pi = para_idx as usize;
        let para: &crate::model::paragraph::Paragraph = if path_json.is_empty() {
            self.document
                .sections
                .get(sec)
                .and_then(|s| s.paragraphs.get(pi))
                .ok_or_else(|| JsValue::from_str("인덱스 범위 초과"))?
        } else {
            let path = DocumentCore::parse_cell_path(path_json)?;
            self.resolve_paragraph_by_path(sec, pi, &path)?
        };
        let off = offset as usize;
        let converted = match mode {
            0 => axis::logical_to_text_offset(para, off).0,
            1 => axis::text_to_logical_offset(para, off),
            2 => axis::caret_to_split_offset(para, off),
            3 => axis::split_to_caret_offset(para, off),
            4 => axis::logical_to_text_offset(para, off).1 as usize,
            5 => axis::split_to_caret_offset(para, usize::MAX),
            _ => return Err(JsValue::from_str("mode 는 0~5")),
        };
        Ok(converted as u32)
    }

    /// [claude-hwpx caret-axis] 켜 두는 동안 글자 삽입이 같은 글자 위치의 인라인 컨트롤 뒤에 들어간다.
    /// 캐럿이 글자처럼 취급 개체 바로 뒤일 때(convertCaretOffset mode 4 가 1) 삽입 호출 앞뒤로 켜고 끈다.
    #[wasm_bindgen(js_name = setInsertAfterInline)]
    pub fn set_insert_after_inline(&self, on: bool) {
        crate::model::paragraph::INSERT_AFTER_INLINE_CONTROLS.with(|flag| flag.set(on));
    }

    /// [claude-hwpx caret-axis] 캐럿 축 범위 삭제(본문). 범위 안 글자처럼 취급 개체도 지운다.
    #[wasm_bindgen(js_name = deleteRangeCaret)]
    pub fn delete_range_caret(
        &mut self,
        section_idx: u32,
        start_para: u32,
        start_offset: u32,
        end_para: u32,
        end_offset: u32,
    ) -> Result<String, JsValue> {
        self.delete_range_caret_native(
            section_idx as usize,
            start_para as usize,
            start_offset as usize,
            end_para as usize,
            end_offset as usize,
            None,
        )
        .map_err(|e| e.into())
    }

    /// [claude-hwpx caret-axis] 캐럿 축 범위 삭제(셀).
    #[wasm_bindgen(js_name = deleteRangeCaretInCell)]
    #[allow(clippy::too_many_arguments)]
    pub fn delete_range_caret_in_cell(
        &mut self,
        section_idx: u32,
        parent_para_idx: u32,
        control_idx: u32,
        cell_idx: u32,
        start_para: u32,
        start_offset: u32,
        end_para: u32,
        end_offset: u32,
    ) -> Result<String, JsValue> {
        self.delete_range_caret_native(
            section_idx as usize,
            start_para as usize,
            start_offset as usize,
            end_para as usize,
            end_offset as usize,
            Some((parent_para_idx as usize, control_idx as usize, cell_idx as usize)),
        )
        .map_err(|e| e.into())
    }

    /// [claude-hwpx caret-axis] 캐럿 축 범위 삭제(셀 경로).
    #[wasm_bindgen(js_name = deleteRangeCaretInCellByPath)]
    #[allow(clippy::too_many_arguments)]
    pub fn delete_range_caret_in_cell_by_path_api(
        &mut self,
        section_idx: u32,
        parent_para_idx: u32,
        path_json: &str,
        start_para: u32,
        start_offset: u32,
        end_para: u32,
        end_offset: u32,
    ) -> Result<String, JsValue> {
        let path = DocumentCore::parse_cell_path(path_json)?;
        self.delete_range_caret_in_cell_by_path(
            section_idx as usize,
            parent_para_idx as usize,
            &path,
            start_para as usize,
            start_offset as usize,
            end_para as usize,
            end_offset as usize,
        )
        .map_err(|e| e.into())
    }

    /// [claude-hwpx caret-axis] 캐럿 축 선택 복사(본문). 범위 안 글자처럼 취급 개체도 담는다.
    #[wasm_bindgen(js_name = copySelectionCaret)]
    pub fn copy_selection_caret(
        &mut self,
        section_idx: u32,
        start_para: u32,
        start_offset: u32,
        end_para: u32,
        end_offset: u32,
    ) -> Result<String, JsValue> {
        self.copy_selection_caret_native(
            section_idx as usize,
            start_para as usize,
            start_offset as usize,
            end_para as usize,
            end_offset as usize,
        )
        .map_err(|e| e.into())
    }

    /// [claude-hwpx caret-axis] 캐럿 축 선택 복사(셀).
    #[wasm_bindgen(js_name = copySelectionCaretInCell)]
    #[allow(clippy::too_many_arguments)]
    pub fn copy_selection_caret_in_cell(
        &mut self,
        section_idx: u32,
        parent_para_idx: u32,
        control_idx: u32,
        cell_idx: u32,
        start_para: u32,
        start_offset: u32,
        end_para: u32,
        end_offset: u32,
    ) -> Result<String, JsValue> {
        self.copy_selection_caret_in_cell_native(
            section_idx as usize,
            parent_para_idx as usize,
            control_idx as usize,
            cell_idx as usize,
            start_para as usize,
            start_offset as usize,
            end_para as usize,
            end_offset as usize,
        )
        .map_err(|e| e.into())
    }

    /// [claude-hwpx caret-axis] 캐럿 축 선택 복사(셀 경로).
    #[wasm_bindgen(js_name = copySelectionCaretInCellByPath)]
    #[allow(clippy::too_many_arguments)]
    pub fn copy_selection_caret_in_cell_by_path_api(
        &mut self,
        section_idx: u32,
        parent_para_idx: u32,
        path_json: &str,
        start_para: u32,
        start_offset: u32,
        end_para: u32,
        end_offset: u32,
    ) -> Result<String, JsValue> {
        let path = DocumentCore::parse_cell_path(path_json)?;
        self.copy_selection_caret_in_cell_by_path_native(
            section_idx as usize,
            parent_para_idx as usize,
            &path,
            start_para as usize,
            start_offset as usize,
            end_para as usize,
            end_offset as usize,
        )
        .map_err(|e| e.into())
    }

