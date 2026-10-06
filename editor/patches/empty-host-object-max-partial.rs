// ==== find ====
                    if rendered_top_and_bottom_non_inline {
                        para_y +=
                            self.paragraph_top_and_bottom_non_inline_flow_height(&para.controls);
                    }
// ==== replace ====
                    if rendered_top_and_bottom_non_inline {
                        // [claude-hwpx empty-host-object-max] 빈 앵커 문단은 max(빈 줄, 개체)
                        let flow =
                            self.paragraph_top_and_bottom_non_inline_flow_height(&para.controls);
                        let overlap = crate::renderer::height_measurer::claude_empty_host_flow_overlap_px(
                            para, flow, self.dpi,
                        );
                        if overlap > 0.0 {
                            para_y = para_y.max(para_y_before_compose + flow);
                        } else {
                            para_y += flow;
                        }
                    }
