// ==== find ====
                                let inc = include_empty
                                    || (include_cell_empty
                                        && cell_para.text.is_empty()
                                        && cell_para.controls.is_empty()
                                        && !cell_diagonal);
// ==== replace ====
                                let inc = include_empty
                                    || (include_cell_empty
                                        && cell_para.text.is_empty()
                                        && cell_para.controls.is_empty()
                                        && !cell_diagonal)
                                    // [claude-hwpx cell-load-inline] 줄 배치 없이 글자처럼 취급 그림, 수식만 든 칸 문단도 다시 조판한다
                                    || Self::claude_inline_object_host_without_segs(cell_para);
// ==== next ====
                            if include_empty && is_rowbreak_table {
                                Self::fit_hwpx_rowbreak_synthetic_cell_lines(
// ==== replace ====
                            Self::claude_reflow_nested_inline_hosts(cell, styles, dpi);
                            if include_empty && is_rowbreak_table {
                                Self::fit_hwpx_rowbreak_synthetic_cell_lines(
// ==== next ====
                if para_is_synthetic(para) && para.line_segs.len() == 1 {
                    Some((idx, para.text.chars().count()))
// ==== replace ====
                if para_is_synthetic(para)
                    && para.line_segs.len() == 1
                    && Self::claude_paragraph_nearly_full(para, styles, dpi)
                {
                    Some((idx, para.text.chars().count()))
// ==== next ====
    fn append_synthetic_cell_line(para: &mut Paragraph, capacity_hint: Option<u32>) -> bool {
// ==== replace ====
    /// [claude-hwpx] 줄 배치 없이 글자처럼 취급하는 그림, 수식만 든 칸 문단. 다시 조판하지 않으면 줄 높이가 0 이라
    /// 칸이 그림 높이를 잃고 그림이 잘린다(2026-10-05 문항카드 그래프 상자, 21494 높이 그림이 한 줄 칸에 눌림).
    fn claude_inline_object_host_without_segs(para: &Paragraph) -> bool {
        para.line_segs.is_empty()
            && !para.controls.is_empty()
            && para.controls.iter().all(|c| match c {
                Control::Picture(p) => p.common.treat_as_char,
                Control::Equation(e) => e.common.treat_as_char,
                _ => false,
            })
    }

    /// [claude-hwpx] 칸 안 표들의 칸까지 내려가 줄 배치 없는 그림, 수식 문단만 다시 조판한다.
    /// 열 때의 칸 재계산은 본문 표의 칸만 돌아, 표 안 표에 든 그래프가 높이 0 줄에 놓였다.
    fn claude_reflow_nested_inline_hosts(
        cell: &mut crate::model::table::Cell,
        styles: &ResolvedStyleSet,
        dpi: f64,
    ) {
        for para in &mut cell.paragraphs {
            for ctrl in &mut para.controls {
                let Control::Table(table) = ctrl else { continue };
                let owner_widths = table.paragraph_frame_owner_widths();
                let table_padding = table.padding;
                for (inner, owner_width) in table.cells.iter_mut().zip(owner_widths) {
                    let frame_padding = inner.paragraph_frame_padding(&table_padding);
                    let inner_width = crate::renderer::composer::cell_inner_text_width(
                        crate::renderer::hwpunit_to_px(owner_width, dpi),
                        crate::renderer::hwpunit_to_px(frame_padding.left as i32, dpi),
                        crate::renderer::hwpunit_to_px(frame_padding.right as i32, dpi),
                        dpi,
                    );
                    for p in &mut inner.paragraphs {
                        if Self::claude_inline_object_host_without_segs(p) {
                            reflow_line_segs(p, ParagraphBox::content_width_px(inner_width, dpi), styles, dpi);
                        }
                    }
                    Self::claude_reflow_nested_inline_hosts(inner, styles, dpi);
                }
            }
        }
    }

    /// [claude-hwpx] 한 줄에 넉넉히 들어가는 문단에는 보강 줄을 붙이지 않는다. 보강 줄은 마지막 글자 앞에서
    /// 끊기므로, 「답하세요.」의 「.」만 다음 줄로 밀리고 앞줄이 양쪽 정렬로 늘어났다(2026-10-05 문항카드,
    /// 줄 배치 없는 HWPX 의 글자처럼 취급 RowBreak 표). 한글이 줄을 하나 더 쓴 문단이라면 글이 상자를 거의 채운다.
    fn claude_paragraph_nearly_full(para: &Paragraph, styles: &ResolvedStyleSet, dpi: f64) -> bool {
        let Some(seg) = para.line_segs.first() else {
            return false;
        };
        if seg.segment_width <= 0 {
            return true;
        }
        let char_shape = para.char_shapes.first().map(|c| c.char_shape_id).unwrap_or(0);
        let style = crate::renderer::layout::resolved_to_text_style(styles, char_shape, 0);
        let width_px = crate::renderer::layout::estimate_text_width_unrounded(&para.text, &style);
        px_to_hwpunit(width_px, dpi) as i64 * 10 >= seg.segment_width as i64 * 9
    }

    fn append_synthetic_cell_line(para: &mut Paragraph, capacity_hint: Option<u32>) -> bool {
