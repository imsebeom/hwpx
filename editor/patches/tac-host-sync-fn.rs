    /// [claude-hwpx tac-host-sync] 칸 편집으로 글자처럼 취급 표의 높이가 바뀌면 표 높이(hp:sz)와 표를 담은
    /// 줄의 높이를 새 높이로 맞춘다. 한글은 둘을 함께 고치는데 rhwp 는 그대로 두어, 표는 커져 그려지는데
    /// 쪽 나누기는 옛 줄 높이만큼만 자리를 잡아 쪽 끝 줄이 본문 영역 밖으로 반 줄 나갔다(2026-09-27 실측,
    /// 한 줄 늘어난 1×1 표 아래 문단). 줄 높이가 「표 높이 + 바깥 여백」인 한글식 문단에서, 문단에 글자처럼
    /// 취급 표가 하나이고 캡션이 없을 때만 고친다.
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
        let Some(seg) = para.line_segs.first() else {
            return;
        };
        let old_h = table.common.height as i32;
        let outer = table.outer_margin_top as i32 + table.outer_margin_bottom as i32;
        if old_h <= 0 || (seg.line_height - (old_h + outer)).abs() > 10 {
            return;
        }
        let measurer = crate::renderer::height_measurer::HeightMeasurer::new(dpi)
            .with_native_hwp5(native_hwp5);
        let new_px = measurer.measure_table_for_edit(table, parent_para_idx, control_idx, &self.styles);
        let new_h = px_to_hwpunit(new_px, dpi);
        if new_h <= 0 || (hwpunit_to_px(new_h - old_h, dpi)).abs() < 1.0 {
            return;
        }
        let para = &mut self.document.sections[section_idx].paragraphs[parent_para_idx];
        if let Some(Control::Table(table)) = para.controls.get_mut(control_idx) {
            table.common.height = new_h as u32;
        }
        if let Some(seg) = para.line_segs.first_mut() {
            let new_lh = new_h + outer;
            if seg.line_height > 0 {
                seg.baseline_distance =
                    (seg.baseline_distance as i64 * new_lh as i64 / seg.line_height as i64) as i32;
            }
            seg.line_height = new_lh;
            seg.text_height = new_lh;
        }
        // 쪽 나누기는 조판해 둔 문단(composed)의 줄 높이를 쓰므로 다시 조판한다(dirty 표시 포함)
        self.recompose_paragraph(section_idx, parent_para_idx);
    }

