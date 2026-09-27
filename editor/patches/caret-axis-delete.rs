    /// [claude-hwpx caret-axis] 캐럿 축 범위 삭제. 가장자리 문단에서 범위 안의 글자처럼 취급 개체(와
    /// 각주, 미주)를 먼저 빼고, 글자는 글자 축으로 옮겨 기존 `delete_range_native` 가 지운다.
    /// 컨트롤을 빼도 글자 번호는 그대로이므로 글자 축 경계는 빼기 전에 잰다. 가운데 문단은
    /// 기존 경로가 통째로 지운다. 반환 위치는 캐럿 축(시작 위치)이다.
    pub fn delete_range_caret_native(
        &mut self,
        section_idx: usize,
        start_para: usize,
        start_caret: usize,
        end_para: usize,
        end_caret: usize,
        cell_ctx: Option<(usize, usize, usize)>,
    ) -> Result<String, HwpError> {
        use super::clipboard::remove_caret_controls_in_range;
        use crate::document_core::helpers::logical_to_text_offset;
        if section_idx >= self.document.sections.len() || start_para > end_para {
            return Err(HwpError::RenderError("삭제 범위 오류".to_string()));
        }
        let (start_text, end_text, removed) = {
            let paras: &mut Vec<Paragraph> = match cell_ctx {
                Some((ppi, ci, cei)) => &mut self.get_cell_mut(section_idx, ppi, ci, cei)?.paragraphs,
                None => &mut self.document.sections[section_idx].paragraphs,
            };
            if end_para >= paras.len() {
                return Err(HwpError::RenderError(format!(
                    "문단 인덱스 범위 초과 (start={}, end={}, 총 {}개)",
                    start_para,
                    end_para,
                    paras.len()
                )));
            }
            let start_text = logical_to_text_offset(&paras[start_para], start_caret).0;
            let end_text = logical_to_text_offset(&paras[end_para], end_caret).0;
            let removed = if start_para == end_para {
                remove_caret_controls_in_range(&mut paras[start_para], start_caret, end_caret)
            } else {
                remove_caret_controls_in_range(&mut paras[end_para], 0, end_caret)
                    + remove_caret_controls_in_range(&mut paras[start_para], start_caret, usize::MAX)
            };
            (start_text, end_text.max(if start_para == end_para { start_text } else { 0 }), removed)
        };
        self.delete_range_native(section_idx, start_para, start_text, end_para, end_text, cell_ctx)?;
        if removed > 0 {
            self.document.sections[section_idx].raw_stream = None;
            match cell_ctx {
                Some((ppi, ci, cei)) => {
                    self.reflow_cell_paragraph(section_idx, ppi, ci, cei, start_para);
                    self.mark_cell_control_dirty(section_idx, ppi, ci);
                    self.mark_section_dirty(section_idx);
                }
                None => {
                    let stored_end_for_reset = crate::renderer::composer::paragraph_flow_end(
                        &self.document.sections[section_idx].paragraphs[start_para],
                    );
                    self.reflow_paragraph(section_idx, start_para);
                    let doc_hwp3_layout = self.document.layout_profile().hwp3_layout();
                    crate::renderer::composer::recalculate_section_vpos(
                        &mut self.document.sections[section_idx].paragraphs,
                        start_para,
                        None,
                        stored_end_for_reset,
                        &self.styles,
                        self.dpi,
                        doc_hwp3_layout,
                    );
                    self.recompose_section(section_idx);
                }
            }
            self.paginate_if_needed();
        }
        Ok(super::super::helpers::json_ok_with(&format!(
            "\"paraIdx\":{},\"charOffset\":{}",
            start_para, start_caret
        )))
    }

    /// [claude-hwpx caret-axis] 경로가 가리키는 셀 안의 캐럿 축 범위 삭제.
    #[allow(clippy::too_many_arguments)]
    pub fn delete_range_caret_in_cell_by_path(
        &mut self,
        section_idx: usize,
        parent_para_idx: usize,
        path: &[(usize, usize, usize)],
        start_para: usize,
        start_caret: usize,
        end_para: usize,
        end_caret: usize,
    ) -> Result<String, HwpError> {
        use super::clipboard::remove_caret_controls_in_range;
        use crate::document_core::helpers::logical_to_text_offset;
        let (start_text, end_text) = {
            let paras = self.get_cell_paragraphs_mut_by_path(section_idx, parent_para_idx, path)?;
            if start_para > end_para || end_para >= paras.len() {
                return Err(HwpError::RenderError("셀 삭제 범위 오류".to_string()));
            }
            let start_text = logical_to_text_offset(&paras[start_para], start_caret).0;
            let end_text = logical_to_text_offset(&paras[end_para], end_caret).0;
            if start_para == end_para {
                remove_caret_controls_in_range(&mut paras[start_para], start_caret, end_caret);
            } else {
                remove_caret_controls_in_range(&mut paras[end_para], 0, end_caret);
                remove_caret_controls_in_range(&mut paras[start_para], start_caret, usize::MAX);
            }
            (start_text, end_text.max(if start_para == end_para { start_text } else { 0 }))
        };
        // 기존 경로 함수가 시작 문단을 늘 다시 흘리고 dirty 를 표시한다
        self.delete_range_in_cell_by_path(
            section_idx,
            parent_para_idx,
            path,
            start_para,
            start_text,
            end_para,
            end_text,
        )?;
        Ok(super::super::helpers::json_ok_with(&format!(
            "\"paraIdx\":{},\"charOffset\":{}",
            start_para, start_caret
        )))
    }

