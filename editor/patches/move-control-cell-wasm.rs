// ==== find ====
            dst as usize,
        )
        .map_err(|e| e.into())
    }

    /// [claude-hwpx caret-axis] 켜 두는 동안 글자 삽입이 같은 글자 위치의 인라인 컨트롤 뒤에 들어간다.
// ==== replace ====
            dst as usize,
        )
        .map_err(|e| e.into())
    }

    /// [claude-hwpx move-control-cell] 칸 안 개체(표 속 표 등)를 같은 칸 문단 자리 dst 로 옮긴다. `table_path_json` 은 개체까지의 칸 경로
    #[wasm_bindgen(js_name = moveControlInCellByPath)]
    pub fn move_control_in_cell_by_path(
        &mut self,
        section_idx: u32,
        parent_para_idx: u32,
        table_path_json: &str,
        dst: u32,
    ) -> Result<String, JsValue> {
        let path = DocumentCore::parse_cell_path(table_path_json)?;
        self.claude_move_control_in_cell(section_idx as usize, parent_para_idx as usize, &path, dst as usize)
            .map_err(|e| e.into())
    }

    /// [claude-hwpx caret-axis] 켜 두는 동안 글자 삽입이 같은 글자 위치의 인라인 컨트롤 뒤에 들어간다.
