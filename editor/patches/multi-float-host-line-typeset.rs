// ==== find ====
            + stored_empty_anchor_host_line_tail;
        let host_spacing = HostSpacing {
// ==== replace ====
            + stored_empty_anchor_host_line_tail;
        // [claude-hwpx multi-float-host-line] 표 둘 이상인 빈 문단의 호스트 줄은 마지막 표 아래에 놓인다
        let after = after
            + self.claude_multi_float_host_line_px(para, ctrl_idx);
        let host_spacing = HostSpacing {
// ==== next ====
    fn flush_deferred_table_controls(
// ==== replace ====
    /// [claude-hwpx multi-float-host-line] HWPX 의 표 둘 이상인 빈 문단에서 이 표가 마지막 표면 호스트 줄 높이(px), 아니면 0
    fn claude_multi_float_host_line_px(&self, para: &Paragraph, ctrl_idx: usize) -> f64 {
        if !self.profile.get().hwpx_container() {
            return 0.0;
        }
        match crate::renderer::claude_multi_float_host_line(para) {
            Some((_, last, hu)) if last == ctrl_idx => hwpunit_to_px(hu, self.dpi),
            _ => 0.0,
        }
    }

    fn flush_deferred_table_controls(
// ==== next ====
            let mt = measured_tables.iter().find(|mt| {
                mt.para_index == deferred.para_index && mt.control_index == deferred.control_index
            });
// ==== replace ====
            // [claude-hwpx multi-float-host-line] 미룬 마지막 표의 호스트 줄은 문단이 시작한 쪽에서 이미 셌다
            let mut ft = ft;
            let claude_host_line = self.claude_multi_float_host_line_px(para, deferred.control_index);
            ft.host_spacing.after -= claude_host_line;
            ft.host_spacing.after_for_fit -= claude_host_line;
            let mt = measured_tables.iter().find(|mt| {
                mt.para_index == deferred.para_index && mt.control_index == deferred.control_index
            });
// ==== next ====
                                para_start_height,
                            });
                            continue;
                        }
                        let pages_before_block_table = st.pages.len();
// ==== replace ====
                                para_start_height,
                            });
                            // [claude-hwpx multi-float-host-line] 마지막 표를 미루면 호스트 줄은 이 쪽(첫 표 아래)에 남는다(d322 p77)
                            st.current_height += self.claude_multi_float_host_line_px(para, ctrl_idx);
                            continue;
                        }
                        let pages_before_block_table = st.pages.len();
// ==== next ====
        let lane_top = lanes.pushed_top(x_start, x_end, raw_top);
        let lane_bottom = lane_top + reserved_height;

        if lane_bottom > available + 0.5 {
            return false;
        }

        st.current_items.push(PageItem::Table {
            para_index: para_idx,
            control_index: ctrl_idx,
        });
        lanes.place(x_start, x_end, raw_top, reserved_height);
// ==== replace ====
        let mut lane_top = lanes.pushed_top(x_start, x_end, raw_top);
        // [claude-hwpx multi-float-host-line] 표 둘 이상인 빈 문단: 첫 표는 문단 위치 + 오프셋 + 바깥 위 여백, 뒤 표는 앞 표 아래(오프셋 없이)
        // + 바깥 위 여백. 예약은 표 높이 + 뒤 간격 전체(바깥 아래 여백, 마지막 표면 호스트 줄)
        let claude_multi = is_topbottom_para_float
            && st.profile.hwpx_container()
            && crate::renderer::claude_multi_float_host_line(para).is_some();
        let mut reserved_height = reserved_height;
        if claude_multi {
            let claude_om_top = hwpunit_to_px(table.outer_margin_top as i32, self.dpi);
            lane_top = if lanes.max_bottom() > 0.0 {
                lanes.max_bottom() + claude_om_top
            } else {
                raw_top + claude_om_top
            };
            reserved_height = ft.effective_height + ft.host_spacing.after;
        }
        let lane_bottom = lane_top + reserved_height;

        if lane_bottom > available + 0.5 {
            return false;
        }

        st.current_items.push(PageItem::Table {
            para_index: para_idx,
            control_index: ctrl_idx,
        });
        lanes.place(
            x_start,
            x_end,
            if claude_multi { lane_top } else { raw_top },
            reserved_height,
        );
