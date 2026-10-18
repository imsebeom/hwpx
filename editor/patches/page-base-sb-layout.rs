// ==== find ====
        let vpos_page_base_init: Option<i32> = col_content.items.first().and_then(|item| {
            match item {
                PageItem::FullParagraph { para_index } => paragraphs
                    .get(*para_index)
                    .and_then(|p| p.line_segs.first())
                    .map(|seg| seg.vertical_pos),
// ==== replace ====
        // [claude-hwpx page-base-sb] 쪽 머리 문단에 그린 위 간격(paragraph_layout 의 쪽 머리 규칙과 같은 값)을 기준점에서 뺀다 — 안 빼면 둘째 문단부터
        // 위 간격만큼 위로 그려진다(d110 7쪽 둘째 문단 −5pt, 한/글 저장본과 새 조판 모두)
        let claude_hwpx = self.profile.get().hwpx_container();
        let claude_top_sb_hu = |para_index: usize, seg: &crate::model::paragraph::LineSeg| -> i32 {
            if !claude_hwpx {
                return 0;
            }
            let sb_hu = paragraphs
                .get(para_index)
                .and_then(|p| styles.para_styles.get(p.para_shape_id as usize))
                .map(|ps| ((ps.spacing_before * 7200.0 / self.dpi).round() as i32).max(0))
                .unwrap_or(0);
            if sb_hu == 0 {
                return 0;
            }
            let v = seg.vertical_pos.max(0);
            let synth = seg.tag & crate::model::paragraph::LineSeg::TAG_IMPLEMENTATION_PROPERTY != 0;
            if para_index == 0 {
                sb_hu.min(v)
            } else if !synth && v <= sb_hu + 38 {
                v
            } else {
                sb_hu
            }
        };
        let vpos_page_base_init: Option<i32> = col_content.items.first().and_then(|item| {
            match item {
                PageItem::FullParagraph { para_index } => paragraphs
                    .get(*para_index)
                    .and_then(|p| p.line_segs.first())
                    .map(|seg| seg.vertical_pos - claude_top_sb_hu(*para_index, seg)),
