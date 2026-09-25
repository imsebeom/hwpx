// ==== find ====
        if json_has_border_keys(props_json) {
            let bf_id = self.create_border_fill_from_json(props_json);
            mods.border_fill_id = Some(bf_id);
        }
        if let Some(arr) = parse_json_i16_array(props_json, "borderSpacing", 4) {
            mods.border_spacing = Some([arr[0], arr[1], arr[2], arr[3]]);
        }

        let new_id;
// ==== replace ====
        if json_has_border_keys(props_json) {
            // [claude-hwpx para-bf-base-cell]
            let cur_ps = self
                .get_cell_paragraph_ref(sec_idx, parent_para_idx, control_idx, cell_idx, cell_para_idx)
                .map(|p| p.para_shape_id)
                .unwrap_or(0);
            let bf_json = self.para_bf_json_with_base(cur_ps, props_json);
            let bf_id = self.create_border_fill_from_json(&bf_json);
            mods.border_fill_id = Some(bf_id);
        }
        if let Some(arr) = parse_json_i16_array(props_json, "borderSpacing", 4) {
            mods.border_spacing = Some([arr[0], arr[1], arr[2], arr[3]]);
        }

        let new_id;
