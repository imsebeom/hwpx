// ==== find ====
        for (si, pi, ci) in targets {
            self.sync_tac_table_host_line(si, pi, ci);
        }
    }
// ==== replace ====
        for (si, pi, ci) in targets {
            // [claude-hwpx tac-nested-sync] 표 속 표부터 맞춘다 — 바깥 표는 칸 문단의 줄 높이(안쪽 표를 담은 줄)로 재므로
            // 안쪽 표가 옛 높이로 남으면 바깥 칸이 커지지 않고, 안쪽 표는 비례 축소로 눌려 그려졌다(2026-10-02 사용자 화면:
            // 표 속 표 칸에 그림을 옮겨 넣자 글줄 순서가 뒤섞이고 그림이 칸 밖으로 나갔다)
            self.claude_sync_nested_tac(si, pi, ci);
            self.sync_tac_table_host_line(si, pi, ci);
        }
    }

    /// [claude-hwpx tac-nested-sync] 본문 표 (si, pi, ci) 안의 글자처럼 취급 표 속 표를 가장 안쪽부터 다시 재어, 내용이
    /// 달라진 표만 적힌 높이와 그 표를 담은 칸 문단 줄 높이를 고치고 칸 안 뒤 줄들의 세로 위치를 그만큼 민다.
    /// 「다시 잰 높이 − 처음 연 때의 어긋남(claude_measure_offset)」을 쓰므로 내용이 그대로인 표는 값이 바뀌지 않는다
    pub(crate) fn claude_sync_nested_tac(&mut self, si: usize, pi: usize, ci: usize) {
        let Some(Control::Table(top)) = self.document.sections.get(si).and_then(|s| s.paragraphs.get(pi)).and_then(|p| p.controls.get(ci)) else {
            return;
        };
        let mut work = top.clone();
        if !self.claude_sync_nested_in(&mut work, pi, ci) {
            return;
        }
        if let Some(Control::Table(t)) = self.document.sections[si].paragraphs[pi].controls.get_mut(ci) {
            *t = work;
        }
    }

    fn claude_sync_nested_in(&self, t: &mut crate::model::table::Table, pi: usize, ci: usize) -> bool {
        use crate::renderer::hwpunit_to_px;
        let mut changed = false;
        for cell in t.cells.iter_mut() {
            for p_idx in 0..cell.paragraphs.len() {
                let tac: Vec<usize> = cell.paragraphs[p_idx]
                    .controls
                    .iter()
                    .enumerate()
                    .filter(|(_, c)| matches!(c, Control::Table(x) if x.common.treat_as_char))
                    .map(|(i, _)| i)
                    .collect();
                for &k in &tac {
                    let (old_h, new_h, outer) = {
                        let Some(Control::Table(child)) = cell.paragraphs[p_idx].controls.get_mut(k) else { continue };
                        changed |= self.claude_sync_nested_in(child, pi, ci);
                        if child.caption.is_some() || child.claude_measure_offset.is_none() {
                            continue;
                        }
                        let old_h = child.common.height as i32;
                        let new_h = self.claude_raw_table_measure(child, pi, ci) - child.claude_measure_offset.unwrap_or(0);
                        if new_h <= 0 || hwpunit_to_px(new_h - old_h, self.dpi).abs() < 1.0 {
                            continue;
                        }
                        child.common.height = new_h as u32;
                        (old_h, new_h, child.outer_margin_top as i32 + child.outer_margin_bottom as i32)
                    };
                    changed = true;
                    // 표를 담은 줄: 표가 하나면 첫 줄, 여럿이면 글 없는 문단에 줄마다 표 하나일 때 그 순번의 줄(본문 sync 와 같은 규칙)
                    let para = &mut cell.paragraphs[p_idx];
                    let text_free = para.text.chars().all(|c| c.is_whitespace() || c.is_control());
                    let seg_idx = if tac.len() == 1 {
                        Some(0)
                    } else if text_free && para.line_segs.len() == tac.len() {
                        tac.iter().position(|&i| i == k)
                    } else {
                        None
                    };
                    let Some(seg_idx) = seg_idx else { continue };
                    let Some(seg) = para.line_segs.get_mut(seg_idx) else { continue };
                    let new_lh = if text_free { new_h + outer } else { seg.line_height + (new_h - old_h) }.max(1);
                    let delta = new_lh - seg.line_height;
                    if seg.line_height > 0 {
                        seg.baseline_distance = (seg.baseline_distance as i64 * new_lh as i64 / seg.line_height as i64) as i32;
                    }
                    seg.line_height = new_lh;
                    seg.text_height = new_lh;
                    // 칸 안 뒤 줄(같은 문단의 뒤 줄, 뒤 문단)의 세로 위치를 민다
                    for s in para.line_segs.iter_mut().skip(seg_idx + 1) {
                        s.vertical_pos += delta;
                    }
                    for q in cell.paragraphs.iter_mut().skip(p_idx + 1) {
                        for s in q.line_segs.iter_mut() {
                            s.vertical_pos += delta;
                        }
                    }
                }
            }
        }
        if changed {
            t.dirty = true;
        }
        changed
    }

    /// [claude-hwpx tac-nested-sync] 처음 쪽을 나눌 때 표 속 표마다 「잰 높이 − 적힌 높이」를 기억한다(본문 표의 claude_init_measure_offsets 와 같은 뜻)
    fn claude_init_nested_in(&self, t: &mut crate::model::table::Table, pi: usize, ci: usize) -> bool {
        let mut changed = false;
        for cell in t.cells.iter_mut() {
            for p in cell.paragraphs.iter_mut() {
                for c in p.controls.iter_mut() {
                    if let Control::Table(child) = c {
                        changed |= self.claude_init_nested_in(child, pi, ci);
                        if child.common.treat_as_char && child.claude_measure_offset.is_none() && child.common.height > 0 {
                            child.claude_measure_offset = Some(self.claude_raw_table_measure(child, pi, ci) - self.claude_opened_table_height(child, pi, ci));
                            changed = true;
                        }
                    }
                }
            }
        }
        changed
    }

    fn claude_has_unmeasured_nested(t: &crate::model::table::Table) -> bool {
        t.cells.iter().flat_map(|c| c.paragraphs.iter()).flat_map(|p| p.controls.iter()).any(|c| match c {
            Control::Table(child) => {
                (child.common.treat_as_char && child.claude_measure_offset.is_none()) || Self::claude_has_unmeasured_nested(child)
            }
            _ => false,
        })
    }
// ==== next ====
    pub(crate) fn claude_init_measure_offsets(&mut self) {
        let mut found = Vec::new();
// ==== replace ====
    pub(crate) fn claude_init_measure_offsets(&mut self) {
        // [claude-hwpx tac-nested-sync] 표 속 표의 어긋남도 기억한다(편집 안 된 본문 표 안만)
        let mut nested = Vec::new();
        for (si, section) in self.document.sections.iter().enumerate() {
            for (pi, para) in section.paragraphs.iter().enumerate() {
                for (ci, ctrl) in para.controls.iter().enumerate() {
                    if let Control::Table(t) = ctrl {
                        if !t.dirty && Self::claude_has_unmeasured_nested(t) {
                            let mut work = t.clone();
                            if self.claude_init_nested_in(&mut work, pi, ci) {
                                nested.push((si, pi, ci, work));
                            }
                        }
                    }
                }
            }
        }
        for (si, pi, ci, work) in nested {
            if let Some(Control::Table(t)) = self.document.sections[si].paragraphs[pi].controls.get_mut(ci) {
                *t = work;
            }
        }
        let mut found = Vec::new();
