    /// [claude-hwpx field-ex-method] 표시 글을 감싼 필드를 넣는다. path 가 비면 본문 문단, 있으면 셀 문단.
    /// kind: hyperlink | crossref | summary. params_xml 은 `<hp:parameters>` 원문(한/글 형식).
    pub fn insert_field_ex_at(
        &mut self,
        section_idx: usize,
        parent_para_idx: usize,
        path: &[(usize, usize, usize)],
        char_offset: usize,
        kind: &str,
        text: &str,
        params_xml: &str,
    ) -> Result<String, HwpError> {
        let (field_type, ctrl_id, properties) = match kind {
            "hyperlink" => (FieldType::Hyperlink, tags::FIELD_HYPERLINK, 0u32),
            "crossref" => (FieldType::CrossRef, tags::FIELD_CROSSREF, 0u32),
            "summary" => (FieldType::Summary, tags::FIELD_SUMMARY, 1u32),
            _ => return Err(HwpError::InvalidField(format!("모르는 필드 종류: {}", kind))),
        };
        // Command 매개변수 값을 command 에도 둔다(HWP 쪽 경로와 필드 조회가 쓴다)
        let command = params_xml
            .split("<hp:stringParam name=\"Command\">")
            .nth(1)
            .and_then(|s| s.split("</hp:stringParam>").next())
            .unwrap_or("")
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">");
        let field_id = self.next_click_here_field_id();
        let (start, end) = if path.is_empty() {
            let section = self
                .document
                .sections
                .get_mut(section_idx)
                .ok_or_else(|| HwpError::InvalidField("구역 인덱스 초과".into()))?;
            section.raw_stream = None;
            let para = section
                .paragraphs
                .get_mut(parent_para_idx)
                .ok_or_else(|| HwpError::InvalidField("문단 인덱스 초과".into()))?;
            insert_field_with_text_in_para(para, char_offset, field_id, field_type, ctrl_id, command, properties, params_xml, text)?
        } else {
            let para = self.get_cell_paragraph_mut_by_path(section_idx, parent_para_idx, path)?;
            insert_field_with_text_in_para(para, char_offset, field_id, field_type, ctrl_id, command, properties, params_xml, text)?
        };
        if path.is_empty() {
            let stored_end_for_reset = crate::renderer::composer::paragraph_flow_end(
                &self.document.sections[section_idx].paragraphs[parent_para_idx],
            );
            self.reflow_paragraph(section_idx, parent_para_idx);
            let doc_hwp3_layout = self.document.layout_profile().hwp3_layout();
            crate::renderer::composer::recalculate_section_vpos(
                &mut self.document.sections[section_idx].paragraphs,
                parent_para_idx,
                None,
                stored_end_for_reset,
                &self.styles,
                self.dpi,
                doc_hwp3_layout,
            );
            self.recompose_paragraph(section_idx, parent_para_idx);
        } else {
            let outer_ctrl = path[0].0;
            let inner_para = path.last().map(|entry| entry.2).unwrap_or(0);
            self.reflow_cell_paragraph_by_path(section_idx, parent_para_idx, path, inner_para);
            self.recalculate_cell_paragraph_vpos_by_path(section_idx, parent_para_idx, path, inner_para, None);
            self.mark_cell_control_dirty(section_idx, parent_para_idx, outer_ctrl);
            if let Some(section) = self.document.sections.get_mut(section_idx) {
                section.raw_stream = None;
            }
            self.mark_section_dirty(section_idx);
        }
        self.paginate_if_needed();
        self.invalidate_page_tree_cache();
        Ok(format!(
            "{{\"ok\":true,\"fieldId\":{},\"start\":{},\"end\":{}}}",
            field_id, start, end
        ))
    }

