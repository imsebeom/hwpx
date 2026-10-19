// ==== find ====
            Some(v) if v > seg.vertical_pos && !curr_has_topbottom_para_table => v,
            _ => prev_vpos_end,
        };
// ==== replace ====
            Some(v) if v > seg.vertical_pos && !curr_has_topbottom_para_table => v,
            // [claude-hwpx host-sa-vpos] HWPX 자리 차지 표 호스트의 vpos 가 앞 문단 끝 + 앞 아래 간격 + 자기 위 간격 안이면 표 높이를
            // 담지 않은 호스트 윗변이다 — 앞 문단 아래 간격을 잃지 않게 그대로 쓴다(d124 p27)
            Some(v)
                if v > prev_vpos_end
                    && curr_has_topbottom_para_table
                    && self.suppress_hwpx_stale_forward
                    && {
                        let px_to_hu = |px: f64| (px.max(0.0) * 7200.0 / self.dpi).round() as i32;
                        let prev_sa_hu = paragraphs
                            .get(prev_pi)
                            .and_then(|p| styles.para_styles.get(p.para_shape_id as usize))
                            .map(|ps| px_to_hu(ps.spacing_after))
                            .unwrap_or(0);
                        let curr_sb_hu = paragraphs
                            .get(item_para)
                            .and_then(|p| styles.para_styles.get(p.para_shape_id as usize))
                            .map(|ps| px_to_hu(ps.spacing_before))
                            .unwrap_or(0);
                        v <= prev_vpos_end + prev_sa_hu + curr_sb_hu + 1
                    } =>
            {
                v
            }
            _ => prev_vpos_end,
        };
