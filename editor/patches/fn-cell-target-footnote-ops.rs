// ==== find ====
impl DocumentCore {
    fn renumber_footnotes_in_section(
// ==== replace ====

/// [claude-hwpx fn-cell-target] 칸 안 각주 위치를 가리키는 가짜 컨트롤 번호의 시작. 이 값 이상이면 claude_fn_cells 목록 번호로 읽는다.
pub(crate) const CLAUDE_FN_CELL_BASE: usize = 0x4000_0000;

/// [claude-hwpx fn-cell-target] 각주 컨트롤(가변). 컨트롤 번호가 CLAUDE_FN_CELL_BASE 이상이면 등록된 칸 안 각주를 찾는다.
pub(crate) fn claude_note_ctrl_mut<'a>(
    doc: &'a mut crate::model::document::Document,
    cells: &[[usize; 5]],
    section_idx: usize,
    para_idx: usize,
    control_idx: usize,
) -> Option<&'a mut Control> {
    let host = doc.sections.get_mut(section_idx)?.paragraphs.get_mut(para_idx)?;
    if control_idx >= CLAUDE_FN_CELL_BASE {
        let [pp, tc, ci, cp, cc] = *cells.get(control_idx - CLAUDE_FN_CELL_BASE)?;
        if pp != para_idx {
            return None;
        }
        match host.controls.get_mut(tc)? {
            Control::Table(t) => t.cells.get_mut(ci)?.paragraphs.get_mut(cp)?.controls.get_mut(cc),
            _ => None,
        }
    } else {
        host.controls.get_mut(control_idx)
    }
}

/// [claude-hwpx fn-cell-target] 각주 컨트롤(읽기).
pub(crate) fn claude_note_ctrl<'a>(
    doc: &'a crate::model::document::Document,
    cells: &[[usize; 5]],
    section_idx: usize,
    para_idx: usize,
    control_idx: usize,
) -> Option<&'a Control> {
    let host = doc.sections.get(section_idx)?.paragraphs.get(para_idx)?;
    if control_idx >= CLAUDE_FN_CELL_BASE {
        let [pp, tc, ci, cp, cc] = *cells.get(control_idx - CLAUDE_FN_CELL_BASE)?;
        if pp != para_idx {
            return None;
        }
        match host.controls.get(tc)? {
            Control::Table(t) => t.cells.get(ci)?.paragraphs.get(cp)?.controls.get(cc),
            _ => None,
        }
    } else {
        host.controls.get(control_idx)
    }
}

impl DocumentCore {
    /// [claude-hwpx fn-cell-target] 칸 안 각주 위치를 등록하고 가짜 컨트롤 번호를 돌려준다(같은 위치는 같은 번호).
    pub fn claude_register_fn_cell(
        &mut self,
        parent_para: usize,
        table_ctrl: usize,
        cell_idx: usize,
        cell_para: usize,
        cell_ctrl: usize,
    ) -> usize {
        let key = [parent_para, table_ctrl, cell_idx, cell_para, cell_ctrl];
        let idx = match self.claude_fn_cells.iter().position(|k| *k == key) {
            Some(i) => i,
            None => {
                self.claude_fn_cells.push(key);
                self.claude_fn_cells.len() - 1
            }
        };
        CLAUDE_FN_CELL_BASE + idx
    }

    fn renumber_footnotes_in_section(
// ==== next ====
        let section = self.document.sections.get_mut(section_idx).ok_or_else(|| {
            HwpError::RenderError(format!("구역 인덱스 {} 범위 초과", section_idx))
        })?;
        let para = section
            .paragraphs
            .get_mut(para_idx)
            .ok_or_else(|| HwpError::RenderError(format!("문단 인덱스 {} 범위 초과", para_idx)))?;
        let ctrl = para.controls.get_mut(control_idx).ok_or_else(|| {
            HwpError::RenderError(format!("컨트롤 인덱스 {} 범위 초과", control_idx))
        })?;
// ==== replace ====
        // [claude-hwpx fn-cell-target] 칸 안 각주(가짜 컨트롤 번호)도 찾는다
        let ctrl = claude_note_ctrl_mut(&mut self.document, &self.claude_fn_cells, section_idx, para_idx, control_idx)
            .ok_or_else(|| HwpError::RenderError(format!("각주 컨트롤 {} 을 찾을 수 없음", control_idx)))?;
// ==== next ====
        let section = self.document.sections.get(section_idx)?;
        let para = section.paragraphs.get(para_idx)?;
        let ctrl = para.controls.get(control_idx)?;
// ==== replace ====
        // [claude-hwpx fn-cell-target]
        let ctrl = claude_note_ctrl(&self.document, &self.claude_fn_cells, section_idx, para_idx, control_idx)?;
// ==== next ====
        let section = &mut self.document.sections[section_idx];
        let ctrl = &mut section.paragraphs[para_idx].controls[control_idx];
// ==== replace ====
        // [claude-hwpx fn-cell-target]
        let Some(ctrl) = claude_note_ctrl_mut(&mut self.document, &self.claude_fn_cells, section_idx, para_idx, control_idx) else {
            return;
        };
// ==== next ====
        let section = self.document.sections.get(section_idx).ok_or_else(|| {
            HwpError::RenderError(format!("구역 인덱스 {} 범위 초과", section_idx))
        })?;
        let para = section
            .paragraphs
            .get(para_idx)
            .ok_or_else(|| HwpError::RenderError(format!("문단 인덱스 {} 범위 초과", para_idx)))?;
        let ctrl = para.controls.get(control_idx).ok_or_else(|| {
            HwpError::RenderError(format!("컨트롤 인덱스 {} 범위 초과", control_idx))
        })?;
// ==== replace ====
        // [claude-hwpx fn-cell-target]
        let ctrl = claude_note_ctrl(&self.document, &self.claude_fn_cells, section_idx, para_idx, control_idx)
            .ok_or_else(|| HwpError::RenderError(format!("각주 컨트롤 {} 을 찾을 수 없음", control_idx)))?;
// ==== next ====
        let mut new_para = {
            let section = self.document.sections.get_mut(section_idx).ok_or_else(|| {
                HwpError::RenderError(format!("구역 인덱스 {} 범위 초과", section_idx))
            })?;
            let para = section.paragraphs.get_mut(para_idx).ok_or_else(|| {
                HwpError::RenderError(format!("문단 인덱스 {} 범위 초과", para_idx))
            })?;
            let ctrl = para.controls.get_mut(control_idx).ok_or_else(|| {
                HwpError::RenderError(format!("컨트롤 인덱스 {} 범위 초과", control_idx))
            })?;
// ==== replace ====
        let mut new_para = {
            // [claude-hwpx fn-cell-target]
            let ctrl = claude_note_ctrl_mut(&mut self.document, &self.claude_fn_cells, section_idx, para_idx, control_idx)
                .ok_or_else(|| HwpError::RenderError(format!("각주 컨트롤 {} 을 찾을 수 없음", control_idx)))?;
// ==== next ====
        let removed_meta;
        {
            let section = self.document.sections.get_mut(section_idx).ok_or_else(|| {
                HwpError::RenderError(format!("구역 인덱스 {} 범위 초과", section_idx))
            })?;
            let para = section.paragraphs.get_mut(para_idx).ok_or_else(|| {
                HwpError::RenderError(format!("문단 인덱스 {} 범위 초과", para_idx))
            })?;
            let ctrl = para.controls.get_mut(control_idx).ok_or_else(|| {
                HwpError::RenderError(format!("컨트롤 인덱스 {} 범위 초과", control_idx))
            })?;
// ==== replace ====
        let removed_meta;
        {
            // [claude-hwpx fn-cell-target]
            let ctrl = claude_note_ctrl_mut(&mut self.document, &self.claude_fn_cells, section_idx, para_idx, control_idx)
                .ok_or_else(|| HwpError::RenderError(format!("각주 컨트롤 {} 을 찾을 수 없음", control_idx)))?;
// ==== next ====
            let ctrl =
                &mut self.document.sections[section_idx].paragraphs[para_idx].controls[control_idx];
// ==== replace ====
            // [claude-hwpx fn-cell-target]
            let ctrl = claude_note_ctrl_mut(&mut self.document, &self.claude_fn_cells, section_idx, para_idx, control_idx)
                .ok_or_else(|| HwpError::RenderError(format!("각주 컨트롤 {} 을 찾을 수 없음", control_idx)))?;
