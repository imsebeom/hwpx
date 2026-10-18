// ==== find ====
    /// 글로벌 쪽 번호에 해당하는 첫 문단 위치 반환
    #[wasm_bindgen(js_name = getPositionOfPage)]
// ==== replace ====
    /// [claude-hwpx fn-cell-target] 표 칸 안 각주 위치를 등록하고 각주 함수에 넘길 가짜 컨트롤 번호를 돌려준다
    #[wasm_bindgen(js_name = registerFootnoteCellTarget)]
    pub fn register_footnote_cell_target(
        &mut self,
        parent_para: u32,
        table_ctrl: u32,
        cell_idx: u32,
        cell_para: u32,
        cell_ctrl: u32,
    ) -> u32 {
        self.core.claude_register_fn_cell(
            parent_para as usize,
            table_ctrl as usize,
            cell_idx as usize,
            cell_para as usize,
            cell_ctrl as usize,
        ) as u32
    }

    /// 글로벌 쪽 번호에 해당하는 첫 문단 위치 반환
    #[wasm_bindgen(js_name = getPositionOfPage)]
