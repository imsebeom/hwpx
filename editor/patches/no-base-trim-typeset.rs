// ==== find ====
                trim_spacing_before_for_flow,
                st.vpos_ladder_dirty || !spacing_trim_restorable(paragraphs, para_idx),
                st.vpos_page_base.is_none() && st.vpos_lazy_base.is_some(),
            );
// ==== replace ====
                trim_spacing_before_for_flow,
                // [claude-hwpx no-base-trim] 쪽(단)에 vpos 기준이 아직 없으면(쪽이 이어지는 표로 시작) 줄인 간격을 되찾을 스냅이 없다.
                // 뒤 문단이 잡는 lazy 기준도 줄인 높이에서 거꾸로 계산하므로 줄인 만큼이 그대로 사라지고, 그리기는 온 높이로 쌓아
                // 표가 본문 아래로 넘쳤다(jidoan 3쪽: 문단 넷이 16px 씩 전진, 그리기는 32.3px, 표 시작 355.1 대 421.9px)
                st.vpos_ladder_dirty
                    || !spacing_trim_restorable(paragraphs, para_idx)
                    || (st.vpos_page_base.is_none() && st.vpos_lazy_base.is_none()),
                st.vpos_page_base.is_none() && st.vpos_lazy_base.is_some(),
            );
