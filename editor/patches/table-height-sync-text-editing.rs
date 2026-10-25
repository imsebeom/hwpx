// ==== find ====
    pub(crate) fn sync_tac_table_host_line(
// ==== replace ====
    /// [claude-hwpx table-height-sync] sync_tac_table_host_line 이 건너뛰는 표의 편집 뒤처리.
    /// ① 글자처럼 취급이 아닌 표: 편집 표식(text_reflowed_after_edit)을 켜 적힌 높이를 행의 바닥으로 쓰지 않게 한다
    ///    (claude_declared_height_stale). rhwp 는 칸 문단에 줄 배치가 다 있으면 적힌 높이를 믿고 행을 늘려, 적힌 높이가 내용보다
    ///    크게 남으면 칸을 줄여도 표가 줄지 않았다(2026-10-25 편집 순서 시험: 글자처럼 취급일 때 커진 높이가 끈 뒤 바닥으로 남아
    ///    2쪽, 같은 파일을 처음부터 조판하면 1쪽, 한글도 1쪽). 적힌 높이 값은 고치지 않는다 — 행 경계 끌기는 그 값에 바뀐 만큼만
    ///    더하는 약속이 있다(issue_1481 시험).
    /// ② 캡션 있는 글자처럼 취급 표: 표 높이를 내용에 맞추고 캡션까지 품은 줄을 다시 짠다(캡션 단 표는 행 높이를 줄여도 표를 담은
    ///    줄이 그대로였다)
    pub(crate) fn claude_sync_table_height_only(
        &mut self,
        section_idx: usize,
        parent_para_idx: usize,
        control_idx: usize,
    ) {
        use crate::renderer::hwpunit_to_px;
        let dpi = self.dpi;
        let Some(Control::Table(table)) = self
            .document
            .sections
            .get(section_idx)
            .and_then(|s| s.paragraphs.get(parent_para_idx))
            .and_then(|p| p.controls.get(control_idx))
        else {
            return;
        };
        if !table.common.treat_as_char {
            if let Some(Control::Table(t)) = self.document.sections[section_idx].paragraphs[parent_para_idx]
                .controls
                .get_mut(control_idx)
            {
                t.text_reflowed_after_edit = true;
            }
            return;
        }
        let old_h = table.common.height as i32;
        let new_h = self.claude_raw_table_measure(table, parent_para_idx, control_idx)
            - table.claude_measure_offset.unwrap_or(0);
        if new_h <= 0 || hwpunit_to_px(new_h - old_h, dpi).abs() < 1.0 {
            return;
        }
        if let Some(Control::Table(t)) = self.document.sections[section_idx].paragraphs[parent_para_idx]
            .controls
            .get_mut(control_idx)
        {
            t.common.height = new_h as u32;
        }
        {
            // 표를 담은 줄이 캡션까지 품으므로 문단을 다시 짜고 뒤 문단 세로 위치를 잇는다(table-props-dirty 와 같다)
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
            // 쪽 나누기는 조판해 둔 문단(composed)의 줄 높이를 쓰므로 다시 조판한다(sync_tac_table_host_line 과 같다).
            // 빠뜨리면 캡션 단 표에 긴 글을 넣었을 때 옛 줄 높이로 맞춤을 판정해 807px 표를 쪽 아래에 그대로 두었다
            self.recompose_paragraph(section_idx, parent_para_idx);
            self.mark_section_dirty(section_idx);
        }
    }

    pub(crate) fn sync_tac_table_host_line(
// ==== next ====
        if !table.common.treat_as_char || table.caption.is_some() {
            return;
        }
// ==== replace ====
        if !table.common.treat_as_char || table.caption.is_some() {
            self.claude_sync_table_height_only(section_idx, parent_para_idx, control_idx);
            return;
        }
// ==== next ====
        for (si, pi, ci) in nested_only {
            self.claude_sync_nested_tac(si, pi, ci);
        }
// ==== replace ====
        for (si, pi, ci) in nested_only {
            self.claude_sync_nested_tac(si, pi, ci);
            // [claude-hwpx table-height-sync] 글자처럼 취급이 아닌 표 자신의 높이도
            self.claude_sync_table_height_only(si, pi, ci);
        }
