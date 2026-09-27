// ==== find ====
        self.reflow_table_cell_paragraphs(section_idx, parent_para_idx, control_idx, &reflow_cells);
// ==== replace ====
        self.reflow_table_cell_paragraphs(section_idx, parent_para_idx, control_idx, &reflow_cells);
        // [claude-hwpx row-resize-th] 스튜디오 Ctrl+위/아래(그려진 높이 기준)면 조절 뒤 표를 다시 재어 표 높이로 둔다
        // (잰 높이 − 처음 잰 어긋남, tac-sync-offset). 적힌 칸 높이 합으로 셈하면 칸 높이가 내용보다 작게 적힌 표에서
        // 표 높이와 행 합이 어긋나, 측정기가 그 차이를 모든 행에 비례로 나누거나 마지막 행에 몰았다
        // (2026-09-28: 고른 두 행만 키웠는데 모든 행이 커졌다). 스튜디오가 보낸 값을 그대로 쓰지 않는 것은,
        // 줄일 때 내용 최소 높이에 걸린 행을 스튜디오가 모르기 때문이다.
        if claude_table_height.is_some() {
            if let Some(h) = self
                .claude_edit_table_height(section_idx, parent_para_idx, control_idx)
                .filter(|h| *h > 0)
            {
                if let Some(Control::Table(t)) = self.document.sections[section_idx].paragraphs
                    [parent_para_idx]
                    .controls
                    .get_mut(control_idx)
                {
                    t.common.height = h as u32;
                    if t.raw_ctrl_data.len() >= common_obj_offsets::HEIGHT.end {
                        t.raw_ctrl_data[common_obj_offsets::HEIGHT]
                            .copy_from_slice(&(h as u32).to_le_bytes());
                    }
                }
            }
        }
