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
        // [claude-hwpx cell-pic-delta] 위 동기화는 그림 칸의 적힌 높이를 「그림 높이 + 여백」으로 덮어쓰고 표 높이를
        // 적힌 칸 높이 합으로 다시 센다. 그러면 칸의 원래 최소 높이가 사라지고 같은 칸의 다른 문단(빈 줄, 설명)이 셈에서
        // 빠져, 그림을 줄이면 설명 칸이 눌리거나(행 233.3/13.4) 오히려 표가 커졌다(2026-09-28 사용자 발견).
        // 글자처럼 취급 표 안 글자처럼 취급 그림이면 칸 높이, 표 높이, 표 줄을 바꾸기 전으로 되돌리고, 칸 문단을 다시 나눠
        // 세로 위치를 매긴 뒤 표 높이는 편집 뒤 표 높이 맞춤(tac-host-sync, 줄 배치 사다리 − 처음 어긋남)에 맡긴다.
        // 행 높이는 칸마다 max(적힌 높이, 내용) 이 된다(tac-row-ladder).
        let mut claude_restored = false;
        if let Some((_, old_tbl_h, old_host_lh, old_cell_h)) = claude_before {
            let (tci, ci, cpi) = path[0];
            if let Some(para) = section.paragraphs.get_mut(parent_para_idx) {
                if let Some(Control::Table(t)) = para.controls.get_mut(tci) {
                    let tac_pic = t
                        .cells
                        .get(ci)
                        .and_then(|c| c.paragraphs.get(cpi))
                        .and_then(|p| p.controls.get(inner_control_idx))
                        .is_some_and(|c| matches!(c, Control::Picture(p) if p.common.treat_as_char));
                    if t.common.treat_as_char && tac_pic {
                        if let Some(cell) = t.cells.get_mut(ci) {
                            cell.height = old_cell_h;
                        }
                        t.common.height = old_tbl_h.max(1) as u32;
                        t.dirty = true;
                        claude_restored = true;
                    }
                }
                if claude_restored {
                    if let Some(seg) = para.line_segs.first_mut() {
                        if seg.line_height > 0 && old_host_lh > 0 {
                            seg.baseline_distance = (seg.baseline_distance as i64 * old_host_lh as i64
                                / seg.line_height as i64) as i32;
                        }
                        seg.line_height = old_host_lh.max(1);
                        seg.text_height = old_host_lh.max(1);
                    }
                }
            }
        }
        section.raw_stream = None;
        // [claude-hwpx cell-pic-delta] 그림이 든 칸 문단의 줄을 새 그림 높이로 다시 나누고, 그 칸 문단들의 세로 위치를 다시 매긴다
        // (옛 그림 높이로 남으면 선택 상자와 행 높이가 어긋났다). 표 높이는 쪽 나누기 앞 표 높이 맞춤이 정한다
        if claude_before.is_some() {
            let (tci, ci, cpi) = path[0];
            self.reflow_cell_paragraph(section_idx, parent_para_idx, tci, ci, cpi);
            if claude_restored {
                self.recalculate_cell_paragraph_vpos_native(section_idx, parent_para_idx, tci, ci, 0, None);
            }
        }
