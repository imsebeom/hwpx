// ==== find ====
        self.document.sections[sec_idx].paragraphs[para_idx].para_shape_id = new_id;
// ==== replace ====
        self.document.sections[sec_idx].paragraphs[para_idx].para_shape_id = new_id;
        // [claude-hwpx parafmt-vpos-chain] 줄 간격, 위아래 간격을 바꾼 문단의 세로 위치를 앞 문단에 잇고 뒤 문단까지 민다. 종전에는
        // 그 문단의 줄만 다시 접고 뒤 문단은 저장 vpos 에 남아, 줄 간격을 160% 에서 70% 로 줄여도 화면이 1px 도 안 움직였다
        // (2026-10-29 결과보고서 Ⅴ장 제목 p222~p225). 다시 접기 전 끝 위치를 잡아 두었다가 글자 서식 경로(charfmt-vpos-chain)처럼 잇는다
        let claude_stored_end = crate::renderer::composer::paragraph_flow_end(
            &self.document.sections[sec_idx].paragraphs[para_idx],
        );
        let claude_rechain = para_shape_mods_affect_text_flow(&mods)
            || mods.spacing_before.is_some()
            || mods.spacing_after.is_some();
// ==== next ====
                ParagraphBox::body_for_style(col_width, para_style, self.dpi),
                &styles,
                self.dpi,
            );
        }

        self.document.sections[sec_idx].raw_stream = None;
// ==== replace ====
                ParagraphBox::body_for_style(col_width, para_style, self.dpi),
                &styles,
                self.dpi,
            );
        }
        if claude_rechain {
            let styles = resolve_styles_for_document(&self.document, self.dpi);
            let hwp3 = self.document.layout_profile().hwp3_layout();
            crate::renderer::composer::recalculate_section_vpos(
                &mut self.document.sections[sec_idx].paragraphs,
                para_idx,
                None,
                claude_stored_end,
                &styles,
                self.dpi,
                hwp3,
            );
        }

        self.document.sections[sec_idx].raw_stream = None;
// ==== next ====
            para.para_shape_id = para_shape_id;
            reflow_line_segs(para, available_box, &styles, self.dpi);
        }
// ==== replace ====
            para.para_shape_id = para_shape_id;
            // [claude-hwpx parafmt-vpos-chain 되돌리기] 문단 모양 되돌리기도 뒤 문단 세로 위치를 함께 되돌린다
            let claude_stored_end = crate::renderer::composer::paragraph_flow_end(para);
            reflow_line_segs(para, available_box, &styles, self.dpi);
            let hwp3 = self.document.layout_profile().hwp3_layout();
            crate::renderer::composer::recalculate_section_vpos(
                &mut self.document.sections[sec_idx].paragraphs,
                para_idx,
                None,
                claude_stored_end,
                &styles,
                self.dpi,
                hwp3,
            );
        }
