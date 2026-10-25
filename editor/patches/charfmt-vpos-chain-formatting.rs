// ==== find ====
            // 원본 LineSeg 무효화 → reflow가 max_font_size에서 새로 계산
            self.document.sections[sec_idx].paragraphs[para_idx]
                .line_segs
                .clear();
            reflow_line_segs(
                &mut self.document.sections[sec_idx].paragraphs[para_idx],
                paragraph_box,
                &styles,
                self.dpi,
            );
        }

        self.document.sections[sec_idx].raw_stream = None;
        self.rebuild_section(sec_idx);
        self.event_log.push(DocumentEvent::CharFormatChanged {
// ==== replace ====
            // [claude-hwpx charfmt-vpos-chain] 다시 접은 문단의 세로 위치를 앞 문단에 잇고 뒤 문단까지 민다. 종전에는 다시 접은
            // 줄이 세로 위치 0 으로 남아 쪽 나누기가 「저장 위치가 되돌아감 = 여기서 쪽이 넘어감」으로 읽어, 글자 크기만 바꿔도
            // 앞뒤 문단의 쪽이 흔들렸다(2026-10-25 편집 일관성 시험 가이드북 2장: p9 글자 크기를 바꾸면 p8 이 2쪽 → 1쪽,
            // 같은 크기로 「바꿔도」 그랬다. 글 편집 경로는 이미 잇는다)
            let stored_end = crate::renderer::composer::paragraph_flow_end(
                &self.document.sections[sec_idx].paragraphs[para_idx],
            );
            // 원본 LineSeg 무효화 → reflow가 max_font_size에서 새로 계산
            self.document.sections[sec_idx].paragraphs[para_idx]
                .line_segs
                .clear();
            reflow_line_segs(
                &mut self.document.sections[sec_idx].paragraphs[para_idx],
                paragraph_box,
                &styles,
                self.dpi,
            );
            let hwp3 = self.document.layout_profile().hwp3_layout();
            crate::renderer::composer::recalculate_section_vpos(
                &mut self.document.sections[sec_idx].paragraphs,
                para_idx,
                None,
                stored_end,
                &self.styles,
                self.dpi,
                hwp3,
            );
        }

        self.document.sections[sec_idx].raw_stream = None;
        self.rebuild_section(sec_idx);
        self.event_log.push(DocumentEvent::CharFormatChanged {
