// ==== find ====
            if rendered_top_and_bottom_non_inline {
                para_y += self.paragraph_top_and_bottom_non_inline_flow_height(&para.controls);
            }
// ==== replace ====
            if rendered_top_and_bottom_non_inline {
                // [claude-hwpx empty-host-object-max] 빈 앵커 문단은 줄과 개체가 겹친다 — 다음 문단은 max(빈 줄, 개체)에서 시작
                let flow = self.paragraph_top_and_bottom_non_inline_flow_height(&para.controls);
                let overlap =
                    crate::renderer::height_measurer::claude_empty_host_flow_overlap_px(para, flow, self.dpi);
                if overlap > 0.0 {
                    para_y = para_y.max(para_y_before_compose + flow);
                } else {
                    para_y += flow;
                }
            }
// ==== next ====
                for para in &cell.paragraphs {
                    text_height +=
                        self.paragraph_top_and_bottom_non_inline_flow_height(&para.controls);
                    for ctrl in &para.controls {
// ==== replace ====
                for para in &cell.paragraphs {
                    // [claude-hwpx empty-host-object-max] 빈 앵커 문단은 줄과 개체의 겹침을 뺀다
                    let flow = self.paragraph_top_and_bottom_non_inline_flow_height(&para.controls);
                    text_height += flow
                        - crate::renderer::height_measurer::claude_empty_host_flow_overlap_px(
                            para, flow, self.dpi,
                        );
                    for ctrl in &para.controls {
