// ==== find ====
            let has_table = self.paragraph_has_table(para);
            if std::env::var("RHWP_DIAG_FLOW").is_ok() {
// ==== replace ====
            // [claude-hwpx overlay-text-host] 글 + 글 앞으로/글 뒤로 1행 표뿐인 문단은 글 문단으로(표는 아래 컨트롤 반복문이 Shape 로 넣는다)
            let has_table = self.paragraph_has_table(para)
                && !(st.profile.hwpx_container()
                    && st.col_count == 1
                    && claude_overlay_text_host(para));
            if std::env::var("RHWP_DIAG_FLOW").is_ok() {
// ==== next ====
                    Control::Footnote(fn_ctrl) => {
                        let source = FootnoteSource::Body {
// ==== replace ====
                    // [claude-hwpx overlay-text-host] 글 문단으로 조판한 글 앞으로/글 뒤로 표는 흐름을 차지하지 않는 개체다(#703 과 같음)
                    Control::Table(t)
                        if !has_table
                            && !t.common.treat_as_char
                            && matches!(
                                t.common.text_wrap,
                                crate::model::shape::TextWrap::InFrontOfText
                                    | crate::model::shape::TextWrap::BehindText
                            ) =>
                    {
                        st.current_items.push(PageItem::Shape {
                            para_index: para_idx,
                            control_index: ctrl_idx,
                        });
                    }
                    Control::Footnote(fn_ctrl) => {
                        let source = FootnoteSource::Body {
// ==== next ====
fn para_is_empty_topbottom_table_anchor(para: &Paragraph) -> bool {
// ==== replace ====
/// [claude-hwpx overlay-text-host] 보이는 글이 있고, 표가 모두 글자처럼 취급이 아닌 1행 글 앞으로/글 뒤로 표인 문단.
/// 표 문단 경로에서는 이 표가 흐름 0 Shape 로 빠져 글줄을 넣을 곳이 없다(소제목 + 「활동결과물」 꼬리표).
fn claude_overlay_text_host(para: &Paragraph) -> bool {
    para_has_non_whitespace_text(para)
        && para.controls.iter().any(|c| matches!(c, Control::Table(_)))
        && para.controls.iter().all(|c| match c {
            Control::Table(t) => {
                !t.common.treat_as_char
                    && t.row_count <= 1
                    && matches!(
                        t.common.text_wrap,
                        crate::model::shape::TextWrap::InFrontOfText
                            | crate::model::shape::TextWrap::BehindText
                    )
            }
            _ => true,
        })
}

fn para_is_empty_topbottom_table_anchor(para: &Paragraph) -> bool {
