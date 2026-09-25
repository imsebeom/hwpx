/// [claude-hwpx field-ex] 표시 글을 감싼 필드(하이퍼링크, 상호 참조, 문서 요약)를 문단에 넣는다.
/// 글을 먼저 넣고, 그 범위를 필드로 감싼다. 매개변수는 한/글이 쓰는 `<hp:parameters>` 원문 그대로 둔다.
fn insert_field_with_text_in_para(
    para: &mut Paragraph,
    char_offset: usize,
    field_id: u32,
    field_type: FieldType,
    ctrl_id: u32,
    command: String,
    properties: u32,
    params_xml: &str,
    text: &str,
) -> Result<(usize, usize), HwpError> {
    let start0 = char_offset.min(para.text.chars().count());
    let start = if text.is_empty() { start0 } else { para.insert_text_at(start0, text) };
    let end = start + text.chars().count();
    let positions = para.control_text_positions();
    let insert_idx = positions
        .iter()
        .position(|&pos| pos > start)
        .unwrap_or(para.controls.len());
    for range in &mut para.field_ranges {
        if range.control_idx >= insert_idx {
            range.control_idx += 1;
        }
    }
    let field = Field {
        field_type,
        command,
        properties,
        extra_properties: 0,
        field_id,
        ctrl_id,
        instance_id: None,
        raw_type: None,
        ctrl_data_name: None,
        memo_index: 0,
        memo_paragraphs: Vec::new(),
        memo_text_direction: None,
        raw_parameters_xml: if params_xml.is_empty() { None } else { Some(params_xml.to_string()) },
        parameters: Default::default(),
        guide_residue: None,
    };
    para.controls.insert(insert_idx, Control::Field(field));
    if para.ctrl_data_records.len() < insert_idx {
        para.ctrl_data_records.resize(insert_idx, None);
    }
    para.ctrl_data_records.insert(insert_idx, None);
    let new_range = FieldRange {
        start_char_idx: start,
        end_char_idx: end,
        control_idx: insert_idx,
        ..Default::default()
    };
    let range_idx = para
        .field_ranges
        .iter()
        .position(|range| {
            range.start_char_idx > start
                || (range.start_char_idx == start && range.control_idx > insert_idx)
        })
        .unwrap_or(para.field_ranges.len());
    para.field_ranges.insert(range_idx, new_range);
    rebuild_char_offsets(para);
    Ok((start, end))
}

