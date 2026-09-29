// ==== find ====
        let section = self.document.sections.get(section_idx)?;
        let host_index = (0..=para_idx).rev().find(|&index| {
            section.paragraphs[index].controls.iter().any(|control| {
                matches!(control, Control::Picture(picture) if !picture.common.treat_as_char)
            })
        })?;
// ==== replace ====
        let section = self.document.sections.get(section_idx)?;
        let has_float = |index: usize| {
            section.paragraphs[index].controls.iter().any(|control| {
                matches!(control, Control::Picture(picture) if !picture.common.treat_as_char)
            })
        };
        let backward = (0..=para_idx).rev().find(|&index| has_float(index));
        // [claude-hwpx wrap-band-backward] 쪽, 종이 기준 그림의 띠는 그림을 품은 문단보다 앞 문단에서 시작할 수 있다 —
        // 뒤쪽 가까운 문단(8개)의 그림도 후보로 본다
        let forward: Vec<usize> = (para_idx + 1..section.paragraphs.len().min(para_idx + 9))
            .filter(|&index| has_float(index))
            .collect();
        for host_index in backward.into_iter().chain(forward) {
            if let Some(found) = self.claude_band_owner_for_host(section_idx, host_index, para_idx) {
                return Some(found);
            }
        }
        None
    }

    /// [claude-hwpx wrap-band-backward] `host_index` 문단의 그림 띠가 `para_idx` 를 포함하면 (호스트, 띠 범위, 단 폭)
    fn claude_band_owner_for_host(
        &self,
        section_idx: usize,
        host_index: usize,
        para_idx: usize,
    ) -> Option<(usize, std::ops::Range<usize>, f64)> {
        let section = self.document.sections.get(section_idx)?;
// ==== next ====
        let new_range = new_band.paragraph_range.clone();
        if new_range.start != host_index || !new_range.contains(&para_idx) {
// ==== replace ====
        let new_range = new_band.paragraph_range.clone();
        // [claude-hwpx wrap-band-backward] 띠는 호스트보다 앞 문단에서 시작할 수 있다
        if new_range.start > host_index || !new_range.contains(&para_idx) {
// ==== next ====
        for released_para_idx in new_range.end..old_range.end {
// ==== replace ====
        // [claude-hwpx wrap-band-backward] 그림이 내려가 띠 앞쪽에서 빠진 문단도 폭 전체로 되돌린다
        for released_para_idx in
            (old_range.start..new_range.start.min(old_range.end)).chain(new_range.end..old_range.end)
        {
// ==== next ====
        let band_lead = staged_paragraphs[host_index]
            .line_segs
            .first()
            .map_or(0, |seg| seg.vertical_pos.max(0));
        crate::renderer::composer::recalculate_section_vpos(
            &mut staged_paragraphs,
            host_index,
            Some(host_index..affected_end),
            stored_host_end,
            &self.styles,
            self.dpi,
            self.document.layout_profile().hwp3_layout(),
        );
        if band_lead > 0 {
            for seg in &mut staged_paragraphs[host_index].line_segs {
                seg.vertical_pos = seg.vertical_pos.saturating_add(band_lead);
            }
            if host_index + 1 < staged_paragraphs.len() {
                crate::renderer::composer::recalculate_section_vpos(
                    &mut staged_paragraphs,
                    host_index + 1,
                    Some(host_index..affected_end),
                    None,
                    &self.styles,
                    self.dpi,
                    self.document.layout_profile().hwp3_layout(),
                );
            }
        }
// ==== replace ====
        // [claude-hwpx wrap-band-backward] 세로 위치는 띠 첫 문단(옛 띠가 더 앞이면 그 문단)부터 다시 매긴다
        let band_first = new_range.start;
        let recalc_from = new_range.start.min(old_range.start);
        let recalc_stored_end = if recalc_from == host_index {
            stored_host_end
        } else {
            crate::renderer::composer::paragraph_flow_end(
                &self.document.sections[section_idx].paragraphs[recalc_from],
            )
        };
        let band_lead = staged_paragraphs[band_first]
            .line_segs
            .first()
            .map_or(0, |seg| seg.vertical_pos.max(0));
        crate::renderer::composer::recalculate_section_vpos(
            &mut staged_paragraphs,
            recalc_from,
            Some(recalc_from..affected_end),
            recalc_stored_end,
            &self.styles,
            self.dpi,
            self.document.layout_profile().hwp3_layout(),
        );
        // 띠 첫 문단이 쪽(단)을 여는 문단이면 세로 위치는 0 부터다(재계산은 앞 쪽 끝에서 이어 붙인다)
        let restart_at = if staged_paragraphs[band_first].column_type
            != crate::model::paragraph::ColumnBreakType::None
        {
            staged_paragraphs[band_first]
                .line_segs
                .first()
                .map_or(0, |seg| seg.vertical_pos)
        } else {
            0
        };
        let shift = band_lead - restart_at;
        if shift != 0 {
            for seg in &mut staged_paragraphs[band_first].line_segs {
                seg.vertical_pos = seg.vertical_pos.saturating_add(shift);
            }
            if band_first + 1 < staged_paragraphs.len() {
                crate::renderer::composer::recalculate_section_vpos(
                    &mut staged_paragraphs,
                    band_first + 1,
                    Some(band_first..affected_end),
                    None,
                    &self.styles,
                    self.dpi,
                    self.document.layout_profile().hwp3_layout(),
                );
            }
        }
