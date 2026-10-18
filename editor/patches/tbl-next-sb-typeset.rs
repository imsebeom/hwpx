// ==== find ====
                self.typeset_paragraph(
                    &mut st,
                    para_idx,
                    para,
                    &formatted,
// ==== replace ====
                // [claude-hwpx tbl-next-sb] 글 없는 문단의 자리 차지 표 바로 뒤 문단은 위 간격을 표 아래에 묻는다(정답본 19/19, lab exp/harvest_tbl_nextsb.py)
                if st.profile.hwpx_container()
                    && formatted.spacing_before > 0.0
                    && para_idx > 0
                    && matches!(st.current_items.last(), Some(PageItem::Table { para_index, .. }) if *para_index + 1 == para_idx)
                    && paragraphs.get(para_idx - 1).is_some_and(|host| {
                        !para_has_non_whitespace_text(host)
                            && host.controls.iter().filter(|c| matches!(c, Control::Table(_))).count() == 1
                            && host.controls.iter().any(|c| matches!(c, Control::Table(t)
                                if crate::renderer::float_placement::is_para_topbottom_float(&t.common)))
                    })
                {
                    st.current_height = (st.current_height - formatted.spacing_before).max(0.0);
                }
                self.typeset_paragraph(
                    &mut st,
                    para_idx,
                    para,
                    &formatted,
