// ==== find ====
                            if let Some((obj_h, extra, h_left, h_right)) = pushdown_h {
// ==== replace ====
                            if let Some((obj_h, extra, h_left, h_right)) = pushdown_h {
                                // [claude-hwpx empty-host-float-pic] 글 없는 문단의 개체 하나는 다음 문단을 max(빈 문단 높이, 오프셋 + 바깥 여백 + 높이 - 다음 문단 위 간격)에 둔다
                                // (harvest_floatpic.py: 그림 6건 모두, 표 241건. d266 p7). 빈 문단 높이(위 간격 + 줄 + 아래 간격)는 이미 더했다
                                let extra = if st.profile.hwpx_container()
                                    && !para_has_visible_text(para)
                                    && para.line_segs.len() <= 1
                                    && para
                                        .controls
                                        .iter()
                                        .filter(|c| matches!(c, Control::Picture(_) | Control::Shape(_) | Control::Table(_)))
                                        .count()
                                        == 1
                                {
                                    let cm = match ctrl {
                                        Control::Picture(p) => Some(&p.common),
                                        Control::Shape(s) => Some(s.common()),
                                        _ => None,
                                    };
                                    cm.map(|cm| {
                                        let obj_hu = signed_hwpunit(cm.vertical_offset).max(0)
                                            + cm.margin.top as i32
                                            + cm.height as i32
                                            + cm.margin.bottom as i32;
                                        let next_sb = paragraphs
                                            .get(para_idx + 1)
                                            .and_then(|np| styles.para_styles.get(np.para_shape_id as usize))
                                            .map(|s| s.spacing_before)
                                            .unwrap_or(0.0);
                                        let own = styles.para_styles.get(para.para_shape_id as usize);
                                        let host_px = own.map(|s| s.spacing_before + s.spacing_after).unwrap_or(0.0)
                                            + para
                                                .line_segs
                                                .first()
                                                .map(|s| hwpunit_to_px(s.line_height + s.line_spacing.max(0), self.dpi))
                                                .unwrap_or(0.0);
                                        (hwpunit_to_px(obj_hu, self.dpi) - next_sb - host_px).max(0.0)
                                    })
                                    .unwrap_or(extra)
                                } else {
                                    extra
                                };
