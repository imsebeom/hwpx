// ==== find ====
            if was_tac || (is_table_or_shape && !is_para_float_table && !is_inline_tac_object) {
                hcursor.vpos_page_base = None;
                hcursor.vpos_lazy_base = None;
            }
// ==== replace ====
            // [claude-hwpx keep-stored-base] 한/글 HWPX 저장 줄 배치는 쪽 기준 절대 좌표 — 쪽 경로 기준점이 서 있고 이 항목 문단 줄이 저장 줄이면 버리지 않는다
            // (버리면 순차 y 로 다시 센 lazy 기준점이 개체 줄 간격만큼 어긋난다. d334 2쪽 p6 표 7.8pt 위)
            let claude_keep_stored_base = self.profile.get().hwpx_container()
                && hcursor.vpos_page_base.is_some()
                && paragraphs
                    .get(item.para_index())
                    .and_then(|p| p.line_segs.first())
                    .is_some_and(|s| s.tag & crate::model::paragraph::LineSeg::TAG_IMPLEMENTATION_PROPERTY == 0);
            if (was_tac || (is_table_or_shape && !is_para_float_table && !is_inline_tac_object))
                && !claude_keep_stored_base
            {
                hcursor.vpos_page_base = None;
                hcursor.vpos_lazy_base = None;
            }
