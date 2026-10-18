// ==== find ====
    fn cell_wrap_objects_bottom_height(&self, paragraphs: &[Paragraph]) -> f64 {
// ==== replace ====
    /// [claude-hwpx nested-cell-flow-pic] 칸 안 위아래 배치(문단 기준) 그림, 도형의 바닥 = 그 문단 첫 줄 위치 + 오프셋 + 바깥 여백 + 높이 의 최댓값.
    /// 저장 줄이 이미 개체 아래로 밀린 문단(첫 줄 vpos >= 앞 문단 끝 + 개체 흐름 높이)은 줄 사다리가 개체를 품었으니 넣지 않는다.
    fn claude_cell_flow_objects_bottom(&self, paragraphs: &[Paragraph]) -> f64 {
        let mut prev_extent = 0.0f64;
        paragraphs
            .iter()
            .map(|p| {
                let first_vpos = p
                    .line_segs
                    .first()
                    .map(|s| hwpunit_to_px(s.vertical_pos, self.dpi))
                    .unwrap_or(prev_extent);
                let flow = p
                    .controls
                    .iter()
                    .map(|ctrl| match ctrl {
                        Control::Picture(pic) if matches!(pic.common.vert_rel_to, VertRelTo::Para) => {
                            self.non_inline_control_flow_height(&pic.common)
                        }
                        Control::Shape(shape) if matches!(shape.common().vert_rel_to, VertRelTo::Para) => {
                            self.non_inline_control_flow_height(shape.common())
                        }
                        _ => 0.0,
                    })
                    .fold(0.0f64, f64::max);
                let absorbed = flow > 0.0 && prev_extent + flow <= first_vpos + 0.5;
                let bottom = if flow > 0.0 && !absorbed { first_vpos + flow } else { 0.0 };
                prev_extent = p
                    .line_segs
                    .iter()
                    .map(|s| hwpunit_to_px(s.vertical_pos.saturating_add(s.line_height.max(0)), self.dpi))
                    .fold(prev_extent, f64::max);
                bottom
            })
            .fold(0.0f64, f64::max)
    }

    fn cell_wrap_objects_bottom_height(&self, paragraphs: &[Paragraph]) -> f64 {
// ==== next ====
                    hwpunit_to_px(last_seg_end, self.dpi)
                        .max(text_height)
                        .max(nested_bottom)
                        .max(self.cell_wrap_objects_bottom_height(&cell.paragraphs))
// ==== replace ====
                    hwpunit_to_px(last_seg_end, self.dpi)
                        .max(text_height)
                        .max(nested_bottom)
                        .max(self.cell_wrap_objects_bottom_height(&cell.paragraphs))
                        // [claude-hwpx nested-cell-flow-pic] 위아래 배치 개체 바닥도(d309 행 3: 그림 16672 를 빼 384.7px, 한/글 593px)
                        .max(self.claude_cell_flow_objects_bottom(&cell.paragraphs))
// ==== next ====
                    let nested_sum =
                        self.unabsorbed_nested_tables_height(&cell.paragraphs, styles, depth);
                    text_height + nested_sum
// ==== replace ====
                    let nested_sum =
                        self.unabsorbed_nested_tables_height(&cell.paragraphs, styles, depth);
                    // [claude-hwpx nested-cell-flow-pic] 줄 배치 없는 칸도 위아래 배치 개체 흐름 높이를 더한다(빈 앵커 문단 줄과는 겹친다)
                    text_height + nested_sum + self.measure_non_inline_controls_height(&cell.paragraphs)
                        - self.claude_empty_host_overlap(&cell.paragraphs)
