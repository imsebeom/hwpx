// ==== find ====
fn reflow_line_segs_impl(
    para: &mut Paragraph,
    paragraph_box: ParagraphBox,
    styles: &ResolvedStyleSet,
    dpi: f64,
    preserve_prefix_for_edit: Option<usize>,
    split_stale_cell_reflow: bool,
) -> bool {
// ==== replace ====
/// [claude-hwpx line-head-flags] 줄마다 글머리(비트 21), 내어쓰기(비트 20) 비트를 한/글 규칙대로 쓴다.
fn claude_set_line_head_flags(para: &mut Paragraph, styles: &ResolvedStyleSet) {
    let Some(st) = styles.para_styles.get(para.para_shape_id as usize) else {
        return;
    };
    let head = st.head_type != crate::model::style::HeadType::None;
    let indent = st.indent;
    for (i, seg) in para.line_segs.iter_mut().enumerate() {
        seg.tag &= !(LineSeg::TAG_PARAGRAPH_HEAD | LineSeg::TAG_INDENTATION);
        if head {
            seg.tag |= if i == 0 { LineSeg::TAG_PARAGRAPH_HEAD } else { LineSeg::TAG_INDENTATION };
        } else if (indent < 0.0 && i > 0) || (indent > 0.0 && i == 0) {
            seg.tag |= LineSeg::TAG_INDENTATION;
        }
    }
}

/// [claude-hwpx line-head-flags] 열 때: 글머리 비트가 규칙과 어긋난 문단만 고친다. 한/글 저장본에는 이런 문단이 없다(정답본 1757줄 예외 0).
/// 옛 에디터 저장본을 다시 저장해도 글머리표가 어긋나지 않게 한다.
pub(crate) fn claude_repair_line_head_flags(paras: &mut [Paragraph], styles: &ResolvedStyleSet) {
    for para in paras.iter_mut() {
        let head = styles
            .para_styles
            .get(para.para_shape_id as usize)
            .is_some_and(|st| st.head_type != crate::model::style::HeadType::None);
        let broken = para.line_segs.iter().enumerate().any(|(i, seg)| {
            (seg.tag & LineSeg::TAG_PARAGRAPH_HEAD != 0) != (head && i == 0)
        });
        if broken {
            claude_set_line_head_flags(para, styles);
        }
        for ctrl in para.controls.iter_mut() {
            if let Control::Table(t) = ctrl {
                for cell in t.cells.iter_mut() {
                    claude_repair_line_head_flags(&mut cell.paragraphs, styles);
                }
            }
        }
    }
}

fn reflow_line_segs_impl(
    para: &mut Paragraph,
    paragraph_box: ParagraphBox,
    styles: &ResolvedStyleSet,
    dpi: f64,
    preserve_prefix_for_edit: Option<usize>,
    split_stale_cell_reflow: bool,
) -> bool {
    let preserved = reflow_line_segs_inner(para, paragraph_box, styles, dpi, preserve_prefix_for_edit, split_stale_cell_reflow);
    claude_set_line_head_flags(para, styles);
    preserved
}

fn reflow_line_segs_inner(
    para: &mut Paragraph,
    paragraph_box: ParagraphBox,
    styles: &ResolvedStyleSet,
    dpi: f64,
    preserve_prefix_for_edit: Option<usize>,
    split_stale_cell_reflow: bool,
) -> bool {
