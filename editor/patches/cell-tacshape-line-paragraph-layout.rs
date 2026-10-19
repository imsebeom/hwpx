// ==== find ====
            } else if has_tac_shape
                && !empty_tac_guide_has_explicit_shape_height
                && (cell_ctx.is_none() || max_fs > 0.0)
                && raw_lh > max_fs * 1.5
// ==== replace ====
            } else if has_tac_shape
                && !empty_tac_guide_has_explicit_shape_height
                && (cell_ctx.is_none() || max_fs > 0.0)
                && raw_lh > max_fs * 1.5
                // [claude-hwpx cell-tacshape-line] 줄 배치 없는 칸 문단의 글 없는 도형 줄은 접지 않는다(칸에는 문단 바닥값 짝이 없다, d317 차례 표)
                && !(cell_ctx.is_some()
                    && runs_all_whitespace
                    && para.is_some_and(crate::renderer::para_has_no_stored_line_segs))
// ==== next ====
            } else if para_index == 0 && !suppress_column_top_vpos_fallback {
                let vpos0_px = para
                    .and_then(|p| p.line_segs.first())
                    .map(|ls| hwpunit_to_px(ls.vertical_pos, self.dpi))
                    .unwrap_or(0.0);
                y += spacing_before.min(vpos0_px.max(0.0));
// ==== replace ====
            } else if para_index == 0 && !suppress_column_top_vpos_fallback {
                let vpos0_px = para
                    .and_then(|p| p.line_segs.first())
                    .map(|ls| hwpunit_to_px(ls.vertical_pos, self.dpi))
                    .unwrap_or(0.0);
                // [claude-hwpx cell-tacshape-line] HWPX 의 엔진이 만든 줄(vpos 0 은 증거가 아님)이면 위 간격을 남긴다 — 한/글은 칸 첫 문단을
                // 늘 위 간격 자리에 둔다(새 정답본 601/601), 쪽 머리도 같다(pagetop-sb-synth)
                if self.profile.get().hwpx_container()
                    && para
                        .and_then(|p| p.line_segs.first())
                        .is_some_and(|ls| ls.tag & LineSeg::TAG_IMPLEMENTATION_PROPERTY != 0)
                {
                    y += spacing_before;
                } else {
                    y += spacing_before.min(vpos0_px.max(0.0));
                }
