// ==== find ====
    link_orphan_field_ends(&mut section.paragraphs);
// ==== replace ====
    link_orphan_field_ends(&mut section.paragraphs);
    // [claude-hwpx memo-list-hwp5] 구역 끝 메모 목록의 본문을 메모 필드에 붙인다
    claude_attach_memo_lists(&records, &mut section.paragraphs);
// ==== next ====
/// 다단락 필드의 종료 마커에 짝 `fieldBegin` 의 id 를 채운다.
// ==== replace ====
/// [claude-hwpx memo-list-hwp5] 구역 끝 MEMO_LIST(메모 번호) → LIST_HEADER → 같은 레벨 문단들을 읽어, 같은 메모 번호의 메모 필드에 본문으로 붙인다.
/// 표 칸, 글상자 안 메모 필드도 찾는다. 이미 본문이 있는 필드는 건드리지 않는다.
fn claude_attach_memo_lists(records: &[Record], paragraphs: &mut [Paragraph]) {
    use crate::model::control::FieldType;
    use std::collections::HashMap;

    let mut lists: HashMap<u32, Vec<Paragraph>> = HashMap::new();
    let mut i = 0;
    while i < records.len() {
        if records[i].tag_id != tags::HWPTAG_MEMO_LIST || records[i].data.len() < 4 {
            i += 1;
            continue;
        }
        let level = records[i].level;
        let d = &records[i].data;
        let index = u32::from_le_bytes([d[0], d[1], d[2], d[3]]);
        i += 1;
        if i < records.len()
            && records[i].tag_id == tags::HWPTAG_LIST_HEADER
            && records[i].level == level
        {
            i += 1;
        }
        let mut paras = Vec::new();
        while i < records.len()
            && records[i].tag_id == tags::HWPTAG_PARA_HEADER
            && records[i].level == level
        {
            let start = i;
            i += 1;
            while i < records.len() && records[i].level > level {
                i += 1;
            }
            if let Ok(p) = parse_paragraph(&records[start..i]) {
                paras.push(p);
            }
        }
        if !paras.is_empty() {
            lists.entry(index).or_insert(paras);
        }
    }
    if lists.is_empty() {
        return;
    }

    fn walk(paras: &mut [Paragraph], lists: &HashMap<u32, Vec<Paragraph>>, depth: usize) {
        if depth > 8 {
            return;
        }
        for para in paras.iter_mut() {
            for ctrl in para.controls.iter_mut() {
                match ctrl {
                    Control::Field(f) => {
                        // 한/글 저장본의 메모 필드는 %me 가 아니라 %unk 이고 명령이 「MEMO/」로 시작한다(실측)
                        let is_memo = f.field_type == FieldType::Memo || f.command.starts_with("MEMO/");
                        if is_memo && f.memo_index != 0 && f.memo_paragraphs.is_empty() {
                            if let Some(body) = lists.get(&f.memo_index) {
                                f.memo_paragraphs = body.clone();
                            }
                        }
                    }
                    Control::Table(t) => {
                        for cell in t.cells.iter_mut() {
                            walk(&mut cell.paragraphs, lists, depth + 1);
                        }
                    }
                    Control::Shape(shape) => {
                        if let Some(tb) = shape.drawing_mut().and_then(|d| d.text_box.as_mut()) {
                            walk(&mut tb.paragraphs, lists, depth + 1);
                        }
                    }
                    _ => {}
                }
            }
        }
    }
    walk(paragraphs, &lists, 0);
}

/// 다단락 필드의 종료 마커에 짝 `fieldBegin` 의 id 를 채운다.
