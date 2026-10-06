// ==== find ====
                };
                let base_x = col_area.x + effective_margin + leading + om_l;
// ==== replace ====
                };
                // [claude-hwpx tac-table-band] 표 줄이 어울림 그림 옆 띠에 있으면(줄 배치의 시작 위치가 문단 여백보다
                // 안쪽) 한/글은 표를 그 띠 안에 놓는다. 띠가 표보다 좁아도 띠 왼쪽에서 시작해 오른쪽으로 넘친다
                // (한국문화 14단원 마지막 쪽: 한/글 재저장 표 줄 horzpos 34627 = 그림 오른쪽, 폭 13561, 표 47624).
                // 종전에는 문단 가운데 정렬로 단 가운데(그림 위)에 그렸다
                let band = para
                    .line_segs
                    .first()
                    .map(|s| (hwpunit_to_px(s.column_start, self.dpi), hwpunit_to_px(s.segment_width, self.dpi)))
                    .filter(|(cs, sw)| *cs > effective_margin + 0.5 && *sw > 0.0);
                if let Some((cs, sw)) = band {
                    let band_x = col_area.x + cs;
                    let tbl_w = hwpunit_to_px(t.common.width as i32, self.dpi);
                    let slack = (sw - tbl_w - om_l - om_r).max(0.0);
                    let x = match para_style.map(|s| s.alignment) {
                        Some(crate::model::style::Alignment::Right) => band_x + slack + om_l,
                        Some(crate::model::style::Alignment::Center) => band_x + slack / 2.0 + om_l,
                        _ => band_x + leading + om_l,
                    };
                    Some(x)
                } else {
                let base_x = col_area.x + effective_margin + leading + om_l;
// ==== next ====
                Some(aligned_x)
            } else {
// ==== replace ====
                Some(aligned_x)
                }
            } else {
