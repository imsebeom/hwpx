// ==== find ====
                y_offset = global_y_before.max(lane_flow_bottom);
            }
            if tac_seg_applied {
// ==== replace ====
                y_offset = global_y_before.max(lane_flow_bottom);
                // [claude-hwpx multi-float-host-line] 표 둘 이상인 빈 문단: 첫 표가 이 쪽에 있고 뒤 표가 이 쪽에 더 없으면 호스트 줄을 이 표 아래에 둔다
                if self.profile.get().hwpx_container() {
                    if let Some((first, last, hu)) = crate::renderer::claude_multi_float_host_line(para) {
                        if control_index >= first && control_index <= last {
                            // 흐름은 쌓인 표 바닥 + 이 표 바깥 아래 여백(첫 표 오프셋과 표마다 여백 위아래가 다 들어간다)
                            if let Some(Control::Table(t)) = para.controls.get(control_index) {
                                y_offset = lanes.max_bottom()
                                    + hwpunit_to_px(t.outer_margin_bottom as i32, self.dpi);
                            }
                            let on_page = |ci: usize| {
                                page_content.column_contents.iter().any(|cc| {
                                    cc.items.iter().any(|it| {
                                        matches!(it, PageItem::Table { para_index: pi, control_index: c }
                                            if *pi == para_index && *c == ci)
                                    })
                                })
                            };
                            if on_page(first) && !(control_index + 1..=last).any(|ci| on_page(ci)) {
                                y_offset += hwpunit_to_px(hu, self.dpi);
                            }
                        }
                    }
                }
            }
            if tac_seg_applied {
// ==== next ====
                    let lane_top = para_float_lanes
                        .entry(para_index)
                        .or_default()
                        .pushed_top(x_start, x_end, raw_top);
                    para_float_lane_info = Some((x_start, x_end, raw_top, lane_top, y_offset));
// ==== replace ====
                    let mut lane_top = para_float_lanes
                        .entry(para_index)
                        .or_default()
                        .pushed_top(x_start, x_end, raw_top);
                    // [claude-hwpx multi-float-host-line] 표 둘 이상인 빈 문단의 뒤 표는 오프셋을 쓰지 않고 앞 표 아래에 쌓인다:
                    // 앞 표 바닥 + 앞 표 바깥 아래 여백 + 이 표 바깥 위 여백(사본 실험 two_om, two_om_off0, two_off375)
                    if self.profile.get().hwpx_container() {
                        if let Some((first, _, _)) = crate::renderer::claude_multi_float_host_line(para) {
                            let lanes_bottom = para_float_lanes
                                .get(&para_index)
                                .map(|l| l.max_bottom())
                                .unwrap_or(0.0);
                            let prev_om_bottom = para.controls[..control_index.min(para.controls.len())]
                                .iter()
                                .rev()
                                .find_map(|c| match c {
                                    Control::Table(pt) => Some(pt.outer_margin_bottom as i32),
                                    _ => None,
                                });
                            if control_index > first && lanes_bottom > 0.0 {
                                if let Some(prev_om_bottom) = prev_om_bottom {
                                    lane_top = lanes_bottom
                                        + hwpunit_to_px(prev_om_bottom, self.dpi)
                                        + hwpunit_to_px(t.outer_margin_top as i32, self.dpi);
                                }
                            }
                        }
                    }
                    para_float_lane_info = Some((x_start, x_end, raw_top, lane_top, y_offset));
// ==== next ====
                lanes.place(x_start, x_end, raw_top, reserved_height);
// ==== replace ====
                // [claude-hwpx multi-float-host-line] 쌓은 뒤 표는 고친 위치(lane_top)로 기록해야 바닥이 맞는다
                let claude_place_top = if self.profile.get().hwpx_container()
                    && crate::renderer::claude_multi_float_host_line(para).is_some()
                {
                    lane_top
                } else {
                    raw_top
                };
                lanes.place(x_start, x_end, claude_place_top, reserved_height);
