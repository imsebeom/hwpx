// ==== find ====
    fn claude_inline_object_host_without_segs(para: &Paragraph) -> bool {
// ==== replace ====
    /// [claude-hwpx cell-para-margin] 칸 문단이 줄을 채울 폭 — 칸 안쪽 폭에서 문단 왼쪽, 오른쪽 여백을 뺀다. 편집 경로
    /// (text_editing.rs 의 final_width)와 같은 식이다. 한/글 2024 도 칸 안에서 문단 여백을 뺀 폭으로 나눈다.
    fn claude_cell_para_width(
        para: &Paragraph,
        inner_px: f64,
        styles: &crate::renderer::style_resolver::ResolvedStyleSet,
    ) -> f64 {
        let style = styles.para_styles.get(para.para_shape_id as usize);
        let margin_left = style.map(|s| s.margin_left).unwrap_or(0.0);
        let margin_right = style.map(|s| s.margin_right).unwrap_or(0.0);
        (inner_px - margin_left - margin_right).max(0.0)
    }

    fn claude_inline_object_host_without_segs(para: &Paragraph) -> bool {
// ==== next ====
        let width_px = crate::renderer::layout::estimate_text_width_unrounded(&para.text, &style);
// ==== replace ====
        // [claude-hwpx cell-para-margin] 한/글은 줄 끝 빈칸을 줄 폭에 넣지 않는다. 문단 여백을 뺀 정확한 폭에서는 끝 빈칸 때문에
        // 「거의 꽉 참」으로 잘못 보고 가짜 둘째 줄을 붙였다(d314 「현  장 」: 끝 빈칸 포함 91%, 빼면 78%).
        let width_px = crate::renderer::layout::estimate_text_width_unrounded(para.text.trim_end(), &style);
// ==== next ====
                                    // 표 소유자가 이미 확정한 셀 폭을 흔든다.
                                    reflow_line_segs(
                                        cell_para,
                                        ParagraphBox::content_width_px(cell_inner_width, dpi),
// ==== replace ====
                                    // 표 소유자가 이미 확정한 셀 폭을 흔든다.
                                    reflow_line_segs(
                                        cell_para,
                                        ParagraphBox::content_width_px(
                                            Self::claude_cell_para_width(cell_para, cell_inner_width, styles),
                                            dpi,
                                        ),
// ==== next ====
                                    // 셀 내용 상자 — 위와 같은 이유로 미스냅.
                                    reflow_line_segs(
                                        cell_para,
                                        ParagraphBox::content_width_px(cell_inner_width, dpi),
// ==== replace ====
                                    // 셀 내용 상자 — 위와 같은 이유로 미스냅.
                                    reflow_line_segs(
                                        cell_para,
                                        ParagraphBox::content_width_px(
                                            Self::claude_cell_para_width(cell_para, cell_inner_width, &styles),
                                            dpi,
                                        ),
