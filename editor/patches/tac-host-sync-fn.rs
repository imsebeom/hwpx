    /// [claude-hwpx tac-host-sync] 칸 편집으로 글자처럼 취급 표의 높이가 바뀌면 표 높이(hp:sz)와 표를 담은
    /// 줄의 높이를 새 높이로 맞춘다. 한글은 둘을 함께 고치는데 rhwp 는 그대로 두어, 표는 커져 그려지는데
    /// 쪽 나누기는 옛 줄 높이만큼만 자리를 잡아 쪽 끝 줄이 본문 영역 밖으로 반 줄 나갔다(2026-09-27 실측,
    /// 한 줄 늘어난 1×1 표 아래 문단). 캡션 없는 표만 고친다.
    /// 둘째 판(같은 날): ① 표는 적힌 높이를 0 으로 둔 사본으로 잰다 — 적힌 높이 그대로 재면 글자처럼 취급 표 비례
    /// 축소가 늘어난 내용을 도로 눌러, 한 줄이 늘면 다른 줄이 그만큼 줄고 표는 그대로였다(프롬프트 표 19.8+102.4 →
    /// 50.0+72.2). ② 「줄 높이 = 표 높이 + 바깥 여백」 관계를 요구하지 않고 줄 높이는 표 높이 변화만큼 더한다
    /// (에디터로 저장한 판은 이 관계가 이미 어긋나 있어 건너뛰었다).
    pub(crate) fn sync_tac_table_host_line(
        &mut self,
        section_idx: usize,
        parent_para_idx: usize,
        control_idx: usize,
    ) {
        use crate::renderer::hwpunit_to_px;
        let dpi = self.dpi;
        let Some(para) = self
            .document
            .sections
            .get(section_idx)
            .and_then(|s| s.paragraphs.get(parent_para_idx))
        else {
            return;
        };
        let tac_ctrls: Vec<usize> = para
            .controls
            .iter()
            .enumerate()
            .filter(|(_, c)| matches!(c, Control::Table(t) if t.common.treat_as_char))
            .map(|(i, _)| i)
            .collect();
        let Some(Control::Table(table)) = para.controls.get(control_idx) else {
            return;
        };
        if !table.common.treat_as_char || table.caption.is_some() {
            return;
        }
        // 표를 담은 줄. 표가 하나면 첫 줄, 여럿이면 글 없는 문단에 줄마다 표 하나(한글 저장 관례)일 때만
        // 그 순번의 줄이다(2026-09-28: 한 문단의 둘째 표가 칸 내용을 따라가지 않아 칸이 표 밖으로 2px 삐졌다).
        let seg_idx = if tac_ctrls.len() == 1 {
            0
        } else if para.text.chars().all(|c| c.is_whitespace() || c.is_control())
            && para.line_segs.len() == tac_ctrls.len()
        {
            match tac_ctrls.iter().position(|&i| i == control_idx) {
                Some(k) => k,
                None => return,
            }
        } else {
            return;
        };
        if para.line_segs.get(seg_idx).is_none() {
            return;
        }
        let old_h = table.common.height as i32;
        // 셋째 판(2026-09-28): 잰 높이에서 처음 잰 어긋남(claude_measure_offset)을 뺀다. rhwp 는 칸 안 표 등을 한글보다
        // 크게 재어, 내용이 그대로여도 칸을 한 번 고치면 표가 한글보다 9~32px 커졌다(한글 PDF 대조: 367.1px 표가 399.7px).
        let new_h = self.claude_raw_table_measure(table, parent_para_idx, control_idx)
            - table.claude_measure_offset.unwrap_or(0);
        // 글 없는 줄(표만 담은 줄)은 한글처럼 「표 높이 + 바깥 여백」으로 맞춘다. 행 추가, 삭제는 표 높이(hp:sz)를
        // 먼저 바꿔 두어, 표 높이 변화만 보면 줄이 옛 높이로 남았다(2026-09-28: 표 498px, 줄 264px 이라 뒤 문단이 쪽 밖으로).
        let outer = table.outer_margin_top as i32 + table.outer_margin_bottom as i32;
        let text_free = para.text.chars().all(|c| c.is_whitespace() || c.is_control());
        let seg_lh = para.line_segs[seg_idx].line_height;
        let line_off = text_free && hwpunit_to_px(seg_lh - (new_h + outer), dpi).abs() >= 1.0;
        if new_h <= 0 || (hwpunit_to_px(new_h - old_h, dpi).abs() < 1.0 && !line_off) {
            return;
        }
        let para = &mut self.document.sections[section_idx].paragraphs[parent_para_idx];
        let old_end = crate::renderer::composer::paragraph_flow_end(para);
        if let Some(Control::Table(table)) = para.controls.get_mut(control_idx) {
            table.common.height = new_h as u32;
        }
        if let Some(seg) = para.line_segs.get_mut(seg_idx) {
            let new_lh = if text_free {
                new_h + outer
            } else {
                seg.line_height + (new_h - old_h)
            }
            .max(1);
            if seg.line_height > 0 {
                seg.baseline_distance =
                    (seg.baseline_distance as i64 * new_lh as i64 / seg.line_height as i64) as i32;
            }
            seg.line_height = new_lh;
            seg.text_height = new_lh;
        }
        self.claude_shift_following_vpos(section_idx, parent_para_idx, old_end);
        // 쪽 나누기는 조판해 둔 문단(composed)의 줄 높이를 쓰므로 다시 조판한다(dirty 표시 포함)
        self.recompose_paragraph(section_idx, parent_para_idx);
        self.mark_section_dirty(section_idx);
    }

    /// [claude-hwpx tac-host-sync] 쪽 나누기 직전에 부른다. 편집으로 dirty 표시가 켜진 본문 글자처럼 취급 표를 모두 맞춘다.
    /// 편집 경로(바꾸기, 글자 모양, 행/열, 크기 조절, 에이전트 도구 …)마다 따로 부르면 빠지는 곳이 생겼다(2026-09-27:
    /// replaceAll 은 표가 안 늘고, 글자 크기 변경은 표만 커지고 쪽이 넘쳤다). dirty 는 편집만 켜고 쪽 나누기가 끝나면 끈다.
    pub(crate) fn claude_sync_dirty_tac_tables(&mut self) {
        self.claude_init_measure_offsets();
        let mut targets = Vec::new();
        for (si, section) in self.document.sections.iter().enumerate() {
            for (pi, para) in section.paragraphs.iter().enumerate() {
                for (ci, ctrl) in para.controls.iter().enumerate() {
                    if let Control::Table(t) = ctrl {
                        if t.dirty && t.common.treat_as_char {
                            targets.push((si, pi, ci));
                        }
                    }
                }
            }
        }
        for (si, pi, ci) in targets {
            self.sync_tac_table_host_line(si, pi, ci);
        }
    }

    /// [claude-hwpx tac-sync-offset] 표를 적힌 높이 0 인 사본으로 잰 높이(HWPUNIT). 적힌 높이로 재면 글자처럼 취급 표
    /// 비례 축소가 늘어난 내용을 도로 누른다.
    pub(crate) fn claude_raw_table_measure(
        &self,
        table: &crate::model::table::Table,
        parent_para_idx: usize,
        control_idx: usize,
    ) -> i32 {
        let mut probe = table.clone();
        probe.common.height = 0;
        // 모든 칸의 문단 세로 위치를 rhwp 로 다시 매긴 뒤 잰다. 편집한 칸만 다시 매겨지므로, 저장 위치(한글) 그대로 잰
        // 기준값과 비교하면 내용이 그대로여도 칸 안 표 때문에 잰 높이가 달라졌다(2026-09-28: 글 하나 넣고 지운 표가 +32px).
        let hwp3 = self.document.layout_profile().hwp3_layout();
        for cell in probe.cells.iter_mut() {
            recalculate_cell_paragraph_vpos(&mut cell.paragraphs, 0, None, &self.styles, self.dpi, hwp3);
        }
        let native_hwp5 = self.document.layout_profile().native_hwp5_layout();
        let px = crate::renderer::height_measurer::HeightMeasurer::new(self.dpi)
            .with_native_hwp5(native_hwp5)
            .measure_table_for_edit(&probe, parent_para_idx, control_idx, &self.styles);
        crate::renderer::px_to_hwpunit(px, self.dpi)
    }

    /// [claude-hwpx tac-sync-offset] 편집한 표의 새 높이(HWPUNIT) = 잰 높이 − 처음 잰 어긋남. 칸 크기 조절도 쓴다.
    pub(crate) fn claude_edit_table_height(
        &self,
        section_idx: usize,
        parent_para_idx: usize,
        control_idx: usize,
    ) -> Option<i32> {
        match self.document.sections.get(section_idx)?.paragraphs.get(parent_para_idx)?.controls.get(control_idx)? {
            Control::Table(t) => Some(
                self.claude_raw_table_measure(t, parent_para_idx, control_idx) - t.claude_measure_offset.unwrap_or(0),
            ),
            _ => None,
        }
    }

    /// [claude-hwpx tac-sync-offset] 아직 안 잰 본문 표마다 「잰 높이 − 적힌 높이」를 기억한다. 처음 쪽을 나눌 때(문서를 연 직후)
    /// 불리므로, 적힌 높이는 한글이 저장한 값이고 그 차이는 rhwp 측정과 한글의 어긋남이다. 편집한(dirty) 표는 건너뛴다.
    pub(crate) fn claude_init_measure_offsets(&mut self) {
        let mut found = Vec::new();
        for (si, section) in self.document.sections.iter().enumerate() {
            for (pi, para) in section.paragraphs.iter().enumerate() {
                for (ci, ctrl) in para.controls.iter().enumerate() {
                    if let Control::Table(t) = ctrl {
                        if t.claude_measure_offset.is_none() && !t.dirty && t.common.height > 0 {
                            let off = self.claude_raw_table_measure(t, pi, ci) - t.common.height as i32;
                            found.push((si, pi, ci, off));
                        }
                    }
                }
            }
        }
        for (si, pi, ci, off) in found {
            if let Some(Control::Table(t)) = self.document.sections[si].paragraphs[pi].controls.get_mut(ci) {
                t.claude_measure_offset = Some(off);
            }
        }
    }

    /// [claude-hwpx tac-host-sync] 문단 from 의 높이가 바뀐 뒤 뒤 문단들의 저장 세로 위치(vertpos)를 다시 매긴다.
    /// 쪽 나누기는 문단마다 저장 vertpos 로 되감아 맞추므로, 그대로 두면 늘어난 만큼이 되감겨 쪽 끝 줄이 넘쳤다
    /// (한글은 뒤 문단을 모두 다시 매긴다). rhwp 의 본문 재계산(recalculate_section_vpos)을 쓰고, 바뀌기 전 문단 끝
    /// stored_end 를 넘긴다.
    pub(crate) fn claude_shift_following_vpos(
        &mut self,
        section_idx: usize,
        from: usize,
        stored_end: Option<i32>,
    ) {
        let hwp3 = self.document.layout_profile().hwp3_layout();
        crate::renderer::composer::recalculate_section_vpos(
            &mut self.document.sections[section_idx].paragraphs,
            from,
            None,
            stored_end,
            &self.styles,
            self.dpi,
            hwp3,
        );
    }

