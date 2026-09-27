// [claude-hwpx caret-axis] 문단에서 컨트롤 하나를 뺀다 — `delete_control_native_impl` 의 문단 몸을 본문과
// 셀에서 함께 쓰도록 떼어 냈다. 거기에 더해 글자 모양 경계와 줄 시작(UTF-16), 필드 범위의 컨트롤
// 번호, 컨트롤 표식도 맞춘다.
pub(crate) fn remove_control_from_para(para: &mut Paragraph, control_idx: usize) {
    if control_idx >= para.controls.len() {
        return;
    }
    let gap_start = crate::document_core::helpers::control_utf16_positions(para)
        .get(control_idx)
        .copied();
    if let Some(gs) = gap_start {
        let threshold = gs + 8;
        for offset in para.char_offsets.iter_mut() {
            if *offset >= threshold {
                *offset -= 8;
            }
        }
        for cs in para.char_shapes.iter_mut() {
            if cs.start_pos >= threshold {
                cs.start_pos -= 8;
            }
        }
        for ls in para.line_segs.iter_mut() {
            if ls.text_start >= threshold {
                ls.text_start -= 8;
            }
        }
    }
    para.controls.remove(control_idx);
    if control_idx < para.ctrl_data_records.len() {
        para.ctrl_data_records.remove(control_idx);
    }
    for range in para.field_ranges.iter_mut() {
        if range.control_idx > control_idx {
            range.control_idx -= 1;
        }
    }
    if para.char_count >= 8 {
        para.char_count -= 8;
    }
    para.control_mask = recompute_clipboard_control_mask(para);
}

/// 캐럿 범위 [from, to) 안의 캐럿 칸 컨트롤(글자처럼 취급 개체, 각주, 미주)을 뺀다. 뺀 수를 돌려준다.
pub(crate) fn remove_caret_controls_in_range(para: &mut Paragraph, from: usize, to: usize) -> usize {
    let slots = crate::document_core::helpers::caret_control_slots(para);
    let mut targets: Vec<usize> = slots
        .iter()
        .enumerate()
        .filter_map(|(ci, slot)| slot.filter(|s| *s >= from && *s < to).map(|_| ci))
        .collect();
    targets.sort_unstable_by(|a, b| b.cmp(a));
    for ci in &targets {
        remove_control_from_para(para, *ci);
    }
    targets.len()
}

/// `clip_paragraph_text_range_for_clipboard` 의 캐럿 축 판. 경계를 나누기 축으로 옮겨 자르므로
/// 캐럿 범위에 든 글자처럼 취급 개체가 복사본에 들어가고, 범위 밖 개체는 빠진다.
pub(crate) fn clip_paragraph_caret_range(
    source: &Paragraph,
    start_caret: usize,
    end_caret: usize,
) -> Paragraph {
    use crate::document_core::helpers::{caret_to_split_offset, logical_to_text_offset};
    let start = logical_to_text_offset(source, start_caret).0;
    let end = logical_to_text_offset(source, end_caret).0.max(start);
    let split_start = caret_to_split_offset(source, start_caret);
    let split_end = caret_to_split_offset(source, end_caret).max(split_start);
    let split_len = caret_to_split_offset(source, usize::MAX);

    let mut clipped = source.clone();
    if split_end < split_len {
        let _ = clipped.split_at(split_end);
    }
    if split_start == 0 {
        return clipped;
    }

    // 남은 컨트롤마다 나누기 칸 — 시작 경계 뒤의 것만 남긴다
    let mut control_split_slot = vec![0usize; clipped.controls.len()];
    {
        let text_len = clipped.text.chars().count();
        let positions = clipped.control_text_positions();
        let mut s = 0usize;
        let mut at: Vec<Vec<usize>> = vec![Vec::new(); text_len + 1];
        for ci in 0..clipped.controls.len() {
            at[positions.get(ci).copied().unwrap_or(text_len).min(text_len)].push(ci);
        }
        for (i, ctrls) in at.iter().enumerate() {
            for &ci in ctrls {
                control_split_slot[ci] = s;
                if Paragraph::is_split_movable_control(&clipped.controls[ci]) {
                    s += 1;
                }
            }
            if i < text_len {
                s += 1;
            }
        }
    }
    let old_controls = clipped.controls.clone();
    let old_records = clipped.ctrl_data_records.clone();
    let old_ranges = clipped.field_ranges.clone();

    let mut suffix = clipped.split_at(split_start);
    let mut keep_control = vec![false; old_controls.len()];
    for range in &old_ranges {
        if range.start_char_idx >= start
            && range.end_char_idx <= end
            && range.control_idx < keep_control.len()
        {
            keep_control[range.control_idx] = true;
        }
    }
    for (idx, ctrl) in old_controls.iter().enumerate() {
        if matches!(
            ctrl,
            Control::SectionDef(_) | Control::ColumnDef(_) | Control::Field(_)
        ) {
            continue;
        }
        if control_split_slot[idx] >= split_start {
            keep_control[idx] = true;
        }
    }

    let mut index_map = vec![None; old_controls.len()];
    let mut new_controls = Vec::new();
    let mut new_records = Vec::new();
    for (old_idx, ctrl) in old_controls.into_iter().enumerate() {
        if !keep_control.get(old_idx).copied().unwrap_or(false) {
            continue;
        }
        index_map[old_idx] = Some(new_controls.len());
        new_records.push(old_records.get(old_idx).cloned().flatten());
        new_controls.push(ctrl);
    }
    let new_field_ranges: Vec<FieldRange> = old_ranges
        .into_iter()
        .filter_map(|mut range| {
            if range.start_char_idx < start || range.end_char_idx > end {
                return None;
            }
            let new_control_idx = index_map.get(range.control_idx).and_then(|idx| *idx)?;
            range.start_char_idx -= start;
            range.end_char_idx -= start;
            range.control_idx = new_control_idx;
            Some(range)
        })
        .collect();

    suffix.controls = new_controls;
    suffix.ctrl_data_records = new_records;
    suffix.field_ranges = new_field_ranges;
    suffix.control_mask = recompute_clipboard_control_mask(&suffix);
    if !suffix.field_ranges.is_empty() {
        rebuild_char_offsets(&mut suffix);
    }
    suffix
}

