// ==== find ====
                    if is_native_picture_caption_float {
                        lanes.max_bottom()
                    } else {
                        global_y_before + reserved_height + physical_ladder_extras_px.unwrap_or(0.0)
                    }
// ==== replace ====
                    // [claude-hwpx empty-float-offset-flow] 저장 줄 배치가 없는 빈 문단(스킬 산출물)의 위아래 배치 표 하나는
                    // 한/글이 다시 조판하며 흐름을 「세로 오프셋 + 바깥 위 여백 + 표 + 바깥 아래 여백」만큼 전진시킨다(#5870 의
                    // 물리 공식). 저장 사다리가 없어 위 #5870 증거 게이트에 안 걸리면 표 높이만 전진해, 표는 오프셋만큼 내려
                    // 그려지는데 다음 문단은 그만큼 위로 올라와 표 아래를 덮었다(2026-10-17 KTX 채점 기준표: 오프셋 893 + 여백
                    // 141×2 = 15.7px. 한/글 재저장본 다음 문단 vpos 차이 39846 = 893+141+38671+141). 줄 배치가 있는 문단은 종전대로
                    let physical_ladder_extras_px = physical_ladder_extras_px.or_else(|| {
                        match para.controls.get(control_index) {
                            Some(Control::Table(table))
                                if crate::renderer::para_has_no_stored_line_segs(para)
                                    && para
                                        .controls
                                        .iter()
                                        .filter(|control| matches!(control, Control::Table(_)))
                                        .count()
                                        == 1 =>
                            {
                                let extras = i64::from(signed_hwpunit(table.common.vertical_offset).max(0))
                                    + i64::from(table.outer_margin_top)
                                    + i64::from(table.outer_margin_bottom);
                                (extras > 0).then(|| hwpunit_to_px(extras as i32, self.dpi))
                            }
                            _ => None,
                        }
                    });
                    if is_native_picture_caption_float {
                        lanes.max_bottom()
                    } else {
                        global_y_before + reserved_height + physical_ladder_extras_px.unwrap_or(0.0)
                    }
