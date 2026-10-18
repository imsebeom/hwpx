// ==== find ====
        || mods.korean_break_unit.is_some()
}
// ==== replace ====
        || mods.korean_break_unit.is_some()
        // [claude-hwpx head-reflow-gate] 번호, 글머리표 머리는 첫 줄 폭을 줄인다(number-head-line-breaking)
        || mods.head_type.is_some()
        || mods.para_level.is_some()
        || mods.numbering_id.is_some()
}
// ==== next ====
            numbering_id: Some(1),
            ..Default::default()
        };
        assert!(!para_shape_mods_affect_text_flow(&mods));
// ==== replace ====
            numbering_id: Some(1),
            ..Default::default()
        };
        // [claude-hwpx head-reflow-gate] 번호 머리 폭을 첫 줄에서 빼므로(number-head-line-breaking) 흐름이 바뀐다
        assert!(para_shape_mods_affect_text_flow(&mods));
