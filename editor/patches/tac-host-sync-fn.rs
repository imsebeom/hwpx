    /// [claude-hwpx tac-host-sync] 칸 편집으로 글자처럼 취급 표의 높이가 바뀌면 표 높이(hp:sz)와 표를 담은
    /// 줄의 높이를 새 높이로 맞춘다. 한글은 둘을 함께 고치는데 rhwp 는 그대로 두어, 표는 커져 그려지는데
    /// 쪽 나누기는 옛 줄 높이만큼만 자리를 잡아 쪽 끝 줄이 본문 영역 밖으로 반 줄 나갔다(2026-09-27 실측,
    /// 한 줄 늘어난 1×1 표 아래 문단). 문단에 글자처럼 취급 표가 하나이고 캡션이 없을 때만 고친다.
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
        use crate::renderer::{hwpunit_to_px, px_to_hwpunit};
        let dpi = self.dpi;
        let native_hwp5 = self.document.layout_profile().native_hwp5_layout();
        let Some(para) = self
            .document
            .sections
            .get(section_idx)
            .and_then(|s| s.paragraphs.get(parent_para_idx))
        else {
            return;
        };
        let tac_count = para
            .controls
            .iter()
            .filter(|c| matches!(c, Control::Table(t) if t.common.treat_as_char))
            .count();
        let Some(Control::Table(table)) = para.controls.get(control_idx) else {
            return;
        };
        if !table.common.treat_as_char || tac_count != 1 || table.caption.is_some() {
            return;
        }
        if para.line_segs.first().is_none() {
            return;
        }
        let old_h = table.common.height as i32;
        let mut probe = table.clone();
        probe.common.height = 0;
        let measurer = crate::renderer::height_measurer::HeightMeasurer::new(dpi)
            .with_native_hwp5(native_hwp5);
        let new_px = measurer.measure_table_for_edit(&probe, parent_para_idx, control_idx, &self.styles);
        let new_h = px_to_hwpunit(new_px, dpi);
        if new_h <= 0 || (hwpunit_to_px(new_h - old_h, dpi)).abs() < 1.0 {
            return;
        }
        let para = &mut self.document.sections[section_idx].paragraphs[parent_para_idx];
        let old_end = crate::renderer::composer::paragraph_flow_end(para);
        if let Some(Control::Table(table)) = para.controls.get_mut(control_idx) {
            table.common.height = new_h as u32;
        }
        if let Some(seg) = para.line_segs.first_mut() {
            let new_lh = (seg.line_height + (new_h - old_h)).max(1);
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

    /// [claude-hwpx tac-host-sync] 문단 from 의 높이가 바뀐 뒤 뒤 문단들의 저장 세로 위치(vertpos)를 다시 매긴다.
    /// 쪽 나누기는 문단마다 저장 vertpos 로 되감아 맞추므로, 그대로 두면 늘어난 만큼이 되감겨 쪽 끝 줄이 넘쳤다
    /// (한글은 뒤 문단을 모두 다시 매긴다). rhwp 의 본문 재계산(recalculate_section_vpos)을 쓰고, 바뀌기 전 문단 끝
    /// stored_end 를 넘겨 낡은 쪽 경계를 알아보게 한다(vpos-stale-reset 패치).
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

