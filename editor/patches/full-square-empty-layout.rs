// ==== find ====
                        Control::Table(t)
                            if is_para_topbottom_float(&t.common) && !para_has_visible_text(para)
                    )
                })
                .unwrap_or(false);
// ==== replace ====
                        Control::Table(t)
                            if is_para_topbottom_float(&t.common) && !para_has_visible_text(para)
                    )
                    // [claude-hwpx full-square-empty] 열을 꽉 채우는 어울림 표의 빈 문단은 자리 차지 표처럼 그린다(d027 p0)
                    || (self.profile.get().hwpx_container()
                        && matches!(c, Control::Table(t)
                            if crate::renderer::claude_full_square_empty_host(para, t)))
                })
                .unwrap_or(false);
// ==== next ====
                if let Some(para_style) = styles.para_styles.get(para_style_id) {
                    if para_style.spacing_after > 0.0 {
                        y_offset += para_style.spacing_after;
// ==== replace ====
                if let Some(para_style) = styles.para_styles.get(para_style_id) {
                    // [claude-hwpx full-square-empty] 열을 꽉 채우는 어울림 표의 빈 문단은 아래 간격이 표 아래에 묻힌다
                    let claude_full_square = self.profile.get().hwpx_container()
                        && matches!(para.controls.get(control_index), Some(Control::Table(t))
                            if crate::renderer::claude_full_square_empty_host(para, t));
                    if para_style.spacing_after > 0.0 && !claude_full_square {
                        y_offset += para_style.spacing_after;
