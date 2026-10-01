// ==== find ====
impl DocumentCore {
    pub(crate) fn get_table_mut(
// ==== replace ====
thread_local! {
    /// [claude-hwpx nested-table-path] 칸 경로(깊이 2 이상)를 켜 둔 동안 칸 크기 조절과 칸 속성 조회가 그 표 속 표를 대상으로 한다.
    /// 평면 API 는 (구역, 문단, 컨트롤)로 맨 바깥 표만 가리켜, 표 속 표 테두리를 끌면 안쪽 칸 번호가 바깥 표에 적용됐다
    /// (상류 devel #7214, #7442 와 같은 목적. 우리 패치 row-resize-th 가 든 본문을 둘로 나누지 않으려고 대상 표만 바꿔 끼운다)
    static CLAUDE_TABLE_PATH: std::cell::RefCell<Option<Vec<(usize, usize, usize)>>> = const { std::cell::RefCell::new(None) };
}

impl DocumentCore {
    fn claude_table_path() -> Option<Vec<(usize, usize, usize)>> {
        CLAUDE_TABLE_PATH.with(|p| p.borrow().clone()).filter(|p| p.len() > 1)
    }

    /// 칸 크기 조절의 대상 표. 칸 경로가 켜져 있으면 그 경로 끝의 표 속 표.
    fn claude_resize_table_mut(
        &mut self,
        section_idx: usize,
        parent_para_idx: usize,
        control_idx: usize,
    ) -> Result<&mut crate::model::table::Table, HwpError> {
        let Some(path) = Self::claude_table_path() else {
            return self.get_table_mut(section_idx, parent_para_idx, control_idx);
        };
        let depth = path.len() - 1;
        let para = self.get_cell_paragraph_mut_by_path(section_idx, parent_para_idx, &path[..depth])?;
        match para.controls.get_mut(path[depth].0) {
            Some(Control::Table(t)) => Ok(t),
            _ => Err(HwpError::RenderError(format!("경로[{}]: controls[{}]가 표가 아닙니다", depth, path[depth].0))),
        }
    }

    /// 표 속 표의 칸 크기를 칸 경로로 조절한다. 경로 끝 항목의 컨트롤이 조절할 표다. 깊이 1 이면 평면 API 와 같다.
    pub fn resize_table_cells_by_path_native(
        &mut self,
        section_idx: usize,
        parent_para_idx: usize,
        path: &[(usize, usize, usize)],
        json: &str,
    ) -> Result<String, HwpError> {
        let Some(&(control_idx, _, _)) = path.last() else {
            return Err(HwpError::RenderError("경로가 비어있습니다".to_string()));
        };
        CLAUDE_TABLE_PATH.with(|p| *p.borrow_mut() = Some(path.to_vec()));
        let r = self.resize_table_cells_native(section_idx, parent_para_idx, control_idx, json);
        CLAUDE_TABLE_PATH.with(|p| *p.borrow_mut() = None);
        r
    }

    /// 표 속 표의 칸 속성을 칸 경로로 읽는다(크기 조절의 최소 크기 검사가 바깥 표 칸을 읽던 것).
    pub fn get_cell_properties_by_path_native(
        &self,
        section_idx: usize,
        parent_para_idx: usize,
        path: &[(usize, usize, usize)],
        cell_idx: usize,
    ) -> Result<String, HwpError> {
        let Some(&(control_idx, _, _)) = path.last() else {
            return Err(HwpError::RenderError("경로가 비어있습니다".to_string()));
        };
        CLAUDE_TABLE_PATH.with(|p| *p.borrow_mut() = Some(path.to_vec()));
        let r = self.get_cell_properties_native(section_idx, parent_para_idx, control_idx, cell_idx);
        CLAUDE_TABLE_PATH.with(|p| *p.borrow_mut() = None);
        r
    }

    pub(crate) fn get_table_mut(
// ==== next ====
        let table = match para.controls.get(control_idx) {
            Some(Control::Table(t)) => t,
            _ => {
                return Err(HwpError::RenderError(
                    "지정된 컨트롤이 표가 아닙니다".to_string(),
                ))
            }
        };

        let cell = table
            .cells
            .get(cell_idx)
            .ok_or_else(|| HwpError::RenderError(format!("셀 인덱스 {} 범위 초과", cell_idx)))?;

        let va = match cell.vertical_align {
// ==== replace ====
        let claude_path = Self::claude_table_path();
        let table = if let Some(path) = claude_path.as_ref() {
            // [claude-hwpx nested-table-path] 칸 경로가 켜져 있으면 표 속 표
            self.resolve_table_by_path(section_idx, parent_para_idx, path)?
        } else {
            match para.controls.get(control_idx) {
                Some(Control::Table(t)) => t,
                _ => {
                    return Err(HwpError::RenderError(
                        "지정된 컨트롤이 표가 아닙니다".to_string(),
                    ))
                }
            }
        };

        let cell = table
            .cells
            .get(cell_idx)
            .ok_or_else(|| HwpError::RenderError(format!("셀 인덱스 {} 범위 초과", cell_idx)))?;

        let va = match cell.vertical_align {
// ==== next ====
        // 셀 업데이트 적용
        let table = self.get_table_mut(section_idx, parent_para_idx, control_idx)?;
        let original_width = table.common.width;
// ==== replace ====
        // 셀 업데이트 적용
        let table = self.claude_resize_table_mut(section_idx, parent_para_idx, control_idx)?;
        let original_width = table.common.width;
// ==== next ====
        let reflow_cells: Vec<(usize, usize)> = {
            let para = &self.document.sections[section_idx].paragraphs[parent_para_idx];
            if let Some(Control::Table(table)) = para.controls.get(control_idx) {
                updates
                    .iter()
                    .filter(|u| u.width_delta != 0)
                    .filter_map(|u| {
                        let pc = table.cells.get(u.cell_idx)?.paragraphs.len();
                        Some((u.cell_idx, pc))
                    })
                    .collect()
            } else {
                Vec::new()
            }
        };
        self.reflow_table_cell_paragraphs(section_idx, parent_para_idx, control_idx, &reflow_cells);
// ==== replace ====
        let reflow_cells: Vec<(usize, usize)> = self
            .claude_resize_table_mut(section_idx, parent_para_idx, control_idx)
            .map(|table| {
                updates
                    .iter()
                    .filter(|u| u.width_delta != 0)
                    .filter_map(|u| {
                        let pc = table.cells.get(u.cell_idx)?.paragraphs.len();
                        Some((u.cell_idx, pc))
                    })
                    .collect()
            })
            .unwrap_or_default();
        let claude_path = Self::claude_table_path();
        if let Some(path) = claude_path.as_ref() {
            // [claude-hwpx nested-table-path] 표 속 표는 안쪽 칸 폭으로 다시 나눈다 — 바깥 칸 폭으로 재면 글줄이 제 칸을 넘는다
            let depth = path.len() - 1;
            let mut inner = path.clone();
            for &(cell_idx, para_count) in &reflow_cells {
                for cell_para_idx in 0..para_count {
                    inner[depth] = (control_idx, cell_idx, cell_para_idx);
                    self.reflow_cell_paragraph_by_path(section_idx, parent_para_idx, &inner, cell_para_idx);
                }
            }
        } else {
            self.reflow_table_cell_paragraphs(section_idx, parent_para_idx, control_idx, &reflow_cells);
        }
// ==== next ====
        if claude_table_height.is_some() {
// ==== replace ====
        // 표 높이 다시 재기는 맨 바깥 표만 한다(표 속 표는 스튜디오가 이 표식을 보내지 않는다)
        if claude_table_height.is_some() && claude_path.is_none() {
