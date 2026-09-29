// ==== find ====
        let affected_end = old_range.end.max(new_range.end);
        crate::renderer::composer::recalculate_section_vpos(
            &mut staged_paragraphs,
            host_index,
            Some(host_index..affected_end),
            stored_host_end,
            &self.styles,
            self.dpi,
            self.document.layout_profile().hwp3_layout(),
        );
// ==== replace ====
        let affected_end = old_range.end.max(new_range.end);
        // [claude-hwpx wrap-band-lead] 띠 줄은 문단 윗변이 0 인 좌표라, 자리 차지 그림처럼 첫 줄이 그림 아래로
        // 내려가면 첫 줄 vpos 가 0 보다 크다. recalculate_section_vpos 는 첫 줄을 문단 시작에 붙여 이 간격을 버리므로
        // (글이 그림 밑으로 겹쳤다) 다시 매긴 뒤 호스트 줄을 그만큼 내리고 뒤 문단을 호스트 끝에서 다시 잇는다
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
