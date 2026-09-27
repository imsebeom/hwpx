// ==== find ====
        Self::sync_direct_owner_cell_for_picture(
            section,
            parent_para_idx,
            &path,
            inner_control_idx,
        )?;
        section.raw_stream = None;
// ==== replace ====
        Self::sync_direct_owner_cell_for_picture(
            section,
            parent_para_idx,
            &path,
            inner_control_idx,
        )?;
        // [claude-hwpx cell-pic-delta] 위 동기화는 표 높이를 「적힌 칸 높이의 합」으로 다시 세는데, 다른 줄 칸이
        // 최소값(예: 1000)만 적고 실제로는 여러 줄이면 표가 내용보다 작게 적혀 글자처럼 취급 표 비례 축소가 걸린다
        // (2026-09-27 실측, 그림 아래 50px 자르기 → 그림 칸 106px 줄고 설명 칸 89.1 → 69.5px 눌림).
        // 글자처럼 취급 표는 원래 표 높이와 줄 높이에 그림 높이 변화만 더한다.
        let mut claude_dh = 0i32;
        let mut claude_old_end: Option<i32> = None;
        if let Some((old_pic_h, old_tbl_h, old_host_lh)) = claude_before {
            let (tci, ci, cpi) = path[0];
            if let Some(para) = section.paragraphs.get_mut(parent_para_idx) {
                let new_pic_h = match para.controls.get(tci) {
                    Some(Control::Table(t)) if t.common.treat_as_char => t
                        .cells
                        .get(ci)
                        .and_then(|c| c.paragraphs.get(cpi))
                        .and_then(|p| p.controls.get(inner_control_idx))
                        .and_then(|c| match c {
                            Control::Picture(p) => Some(p.common.height as i32),
                            _ => None,
                        }),
                    _ => None,
                };
                if let Some(new_pic_h) = new_pic_h {
                    let dh = new_pic_h - old_pic_h;
                    if dh != 0 {
                        if let Some(Control::Table(t)) = para.controls.get_mut(tci) {
                            t.common.height = (old_tbl_h + dh).max(1) as u32;
                        }
                        if let Some(seg) = para.line_segs.first_mut() {
                            let lh = (old_host_lh + dh).max(1);
                            if seg.line_height > 0 {
                                seg.baseline_distance = (seg.baseline_distance as i64 * lh as i64
                                    / seg.line_height as i64)
                                    as i32;
                            }
                            claude_dh = lh - seg.line_height;
                            claude_old_end = Some(seg.vertical_pos + old_host_lh + seg.line_spacing);
                            seg.line_height = lh;
                            seg.text_height = lh;
                        }
                    }
                }
            }
        }
        section.raw_stream = None;
        // 뒤 문단 저장 vertpos 도 다시 매긴다(쪽 나누기의 되감기 방지, tac-host-sync 도우미)
        if claude_dh != 0 {
            self.claude_shift_following_vpos(section_idx, parent_para_idx, claude_old_end);
        }
        // [claude-hwpx cell-pic-delta] 그림이 든 칸 문단의 줄 높이가 옛 그림 높이로 남아 선택 상자가 어긋났다
        if claude_before.is_some() {
            let (tci, ci, cpi) = path[0];
            self.reflow_cell_paragraph(section_idx, parent_para_idx, tci, ci, cpi);
        }
