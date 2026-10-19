// ==== find ====
            let has_stored_para_anchor =
                !local_vpos_restart_seen && crate::renderer::first_seg_vpos_is_anchor(para, cp_idx);
// ==== replace ====
            // [claude-hwpx cell-tacshape-line] 엔진이 합성한 칸 줄의 vpos(모두 0)는 저장 앵커가 아니다 — 첫 문단도 흐름(위 간격)을 따른다
            let has_stored_para_anchor = !local_vpos_restart_seen
                && crate::renderer::first_seg_vpos_is_anchor(para, cp_idx)
                && !(self.profile.get().hwpx_container()
                    && crate::renderer::para_has_no_stored_line_segs(para));
