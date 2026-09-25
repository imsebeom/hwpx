// ==== find ====
        if json_has_border_keys(props_json) {
            let bf_id = self.create_border_fill_from_json(props_json);
            mods.border_fill_id = Some(bf_id);
        }
        if let Some(arr) = parse_json_i16_array(props_json, "borderSpacing", 4) {
            mods.border_spacing = Some([arr[0], arr[1], arr[2], arr[3]]);
        }

        let base_id = self.document.sections[sec_idx].paragraphs[para_idx].para_shape_id;
// ==== replace ====
        if json_has_border_keys(props_json) {
            // [claude-hwpx para-bf-base-body]
            let cur_ps = self.document.sections[sec_idx].paragraphs[para_idx].para_shape_id;
            let bf_json = self.para_bf_json_with_base(cur_ps, props_json);
            let bf_id = self.create_border_fill_from_json(&bf_json);
            mods.border_fill_id = Some(bf_id);
        }
        if let Some(arr) = parse_json_i16_array(props_json, "borderSpacing", 4) {
            mods.border_spacing = Some([arr[0], arr[1], arr[2], arr[3]]);
        }

        let base_id = self.document.sections[sec_idx].paragraphs[para_idx].para_shape_id;
