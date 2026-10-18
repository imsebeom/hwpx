// ==== find ====
                        self.start_new_column_band(&mut st, para_idx, paragraphs);
                    } else {
                        st.advance_column_or_new_page();
                    }
// ==== replace ====
                        self.start_new_column_band(&mut st, para_idx, paragraphs);
                    } else if st.col_count == 1
                        && matches!(st.current_items.last(), Some(PageItem::PartialTable { para_index, is_continuation: true, .. })
                            if *para_index + 1 == para_idx)
                    {
                        // [claude-hwpx colbreak-after-split-table] 여러 쪽에 걸쳐 나뉜 표 바로 다음 문단의 단 나누기는 한/글이 무시한다(e37: d058 변형 셋).
                        // 표가 한 쪽에 들어가거나 사이에 다른 문단이 있으면 지킨다(아래 종전 경로)
                    } else {
                        st.advance_column_or_new_page();
                    }
