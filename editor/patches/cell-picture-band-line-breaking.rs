// ==== find ====
/// [claude-hwpx load-picture-band] 열 때 합성 줄을 띠로 짤 때는
// ==== replace ====
/// [claude-hwpx cell-picture-band] 줄 배치를 합성한 칸(표 속 표 포함)의 어울림 그림 옆 문단을 그림 띠 줄로 바꾼다.
pub(crate) fn claude_cell_picture_bands(paras: &mut [Paragraph], styles: &ResolvedStyleSet, dpi: f64) {
    for para in paras.iter_mut() {
        for ctrl in para.controls.iter_mut() {
            let Control::Table(table) = ctrl else {
                continue;
            };
            let owner_widths = table.paragraph_frame_owner_widths();
            let table_padding = table.padding;
            for (cell, owner_width) in table.cells.iter_mut().zip(owner_widths) {
                claude_cell_picture_bands(&mut cell.paragraphs, styles, dpi);
                let synth = |p: &Paragraph| p.line_segs.iter().all(|s| s.tag & LineSeg::TAG_IMPLEMENTATION_PROPERTY != 0);
                if !cell.paragraphs.iter().all(synth) {
                    continue;
                }
                let padding = cell.paragraph_frame_padding(&table_padding);
                let inner = crate::renderer::composer::cell_inner_text_width(
                    crate::renderer::hwpunit_to_px(owner_width, dpi),
                    crate::renderer::hwpunit_to_px(padding.left as i32, dpi),
                    crate::renderer::hwpunit_to_px(padding.right as i32, dpi),
                    dpi,
                );
                let mut hi = 0usize;
                while hi < cell.paragraphs.len() {
                    let is_host = cell.paragraphs[hi].controls.iter().any(|c| {
                        matches!(c, Control::Picture(p) if !p.common.treat_as_char
                            && p.common.text_wrap == crate::model::shape::TextWrap::Square)
                    });
                    let band = is_host
                        .then(|| claude_layout_picture_band_to_doc_end(&cell.paragraphs, hi, inner, styles, dpi))
                        .flatten();
                    let Some(band) = band else {
                        hi += 1;
                        continue;
                    };
                    let range = band.paragraph_range.clone();
                    for (pi, segs) in range.clone().zip(band.line_segs) {
                        cell.paragraphs[pi].replace_line_segs(segs);
                    }
                    hi = range.end.max(hi + 1);
                }
            }
        }
    }
}

/// [claude-hwpx load-picture-band] 열 때 합성 줄을 띠로 짤 때는
