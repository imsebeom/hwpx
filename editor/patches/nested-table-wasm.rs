    /// [claude-hwpx nested-table-wasm] 표 속 표의 칸 크기를 칸 경로로 조절한다(배치).
    ///
    /// cell_path_json: hitTest 의 cellPath. 마지막 항목의 controlIndex 가 조절할 표다. json 은 resizeTableCells 와 같다.
    #[wasm_bindgen(js_name = resizeTableCellsByPath)]
    pub fn resize_table_cells_by_path(
        &mut self,
        section_idx: u32,
        parent_para_idx: u32,
        cell_path_json: &str,
        json: &str,
    ) -> Result<String, JsValue> {
        let path = parse_cell_path_arg(cell_path_json)?;
        self.resize_table_cells_by_path_native(section_idx as usize, parent_para_idx as usize, &path, json)
            .map_err(|e| e.into())
    }

    /// [claude-hwpx nested-table-wasm] 표 속 표의 칸 속성을 칸 경로로 조회한다. 반환은 getCellProperties 와 같다.
    #[wasm_bindgen(js_name = getCellPropertiesByPath)]
    pub fn get_cell_properties_by_path(
        &self,
        section_idx: u32,
        parent_para_idx: u32,
        cell_path_json: &str,
        cell_idx: u32,
    ) -> Result<String, JsValue> {
        let path = parse_cell_path_arg(cell_path_json)?;
        self.get_cell_properties_by_path_native(section_idx as usize, parent_para_idx as usize, &path, cell_idx as usize)
            .map_err(|e| e.into())
    }

