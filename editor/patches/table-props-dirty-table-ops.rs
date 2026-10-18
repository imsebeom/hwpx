// ==== find ====
        self.document.sections[section_idx].raw_stream = None;
        self.recompose_section(section_idx);
        self.paginate_if_needed();

        if caption_created {
// ==== replace ====
        // [claude-hwpx table-props-dirty] 캡션, 바깥 여백, 크기 같은 속성은 표 높이를 바꾼다. dirty 가 꺼져 있으면 측정기가 옛 높이를 다시 쓴다
        if let Ok(t) = self.get_table_mut(section_idx, parent_para_idx, control_idx) {
            t.dirty = true;
        }
        // 캡션을 켜거나 끈 글자처럼 취급 표는 표를 담은 줄이 캡션만큼 자라거나 줄어야 한다(sync_tac_table_host_line 은
        // 캡션 표를 건너뛴다). 문서를 열 때처럼 그 문단을 다시 짜고 뒤 문단 세로 위치를 잇는다
        if (caption_created || caption_changed)
            && matches!(
                self.document.sections[section_idx].paragraphs[parent_para_idx].controls.get(control_idx),
                Some(crate::model::control::Control::Table(t)) if t.common.treat_as_char
            )
        {
            let stored_end = crate::renderer::composer::paragraph_flow_end(
                &self.document.sections[section_idx].paragraphs[parent_para_idx],
            );
            self.reflow_paragraph(section_idx, parent_para_idx);
            let hwp3 = self.document.layout_profile().hwp3_layout();
            crate::renderer::composer::recalculate_section_vpos(
                &mut self.document.sections[section_idx].paragraphs,
                parent_para_idx,
                None,
                stored_end,
                &self.styles,
                self.dpi,
                hwp3,
            );
        }
        self.document.sections[section_idx].raw_stream = None;
        self.recompose_section(section_idx);
        self.paginate_if_needed();

        if caption_created {
