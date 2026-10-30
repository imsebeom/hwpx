// ==== find ====
    let mut memo_lists = Vec::new();
    for para in &section.paragraphs {
        for ctrl in &para.controls {
            if let Control::Field(field) = ctrl {
                if field.field_type == crate::model::control::FieldType::Memo
                    && !field.memo_paragraphs.is_empty()
                {
                    memo_lists.push((field.memo_index, field.memo_paragraphs.clone()));
                }
            }
        }
    }
    memo_lists
}
// ==== replace ====
    // [claude-hwpx memo-list-cells] 표 칸(표 속 표 포함) 안의 메모도 모은다. 안 그러면 다시 열 때 본문이 사라진다
    fn walk(paras: &[Paragraph], out: &mut Vec<(u32, Vec<Paragraph>)>) {
        for para in paras {
            for ctrl in &para.controls {
                match ctrl {
                    Control::Field(field)
                        if (field.field_type == crate::model::control::FieldType::Memo
                            || field.command.starts_with("MEMO/"))
                            && !field.memo_paragraphs.is_empty() =>
                    {
                        out.push((field.memo_index, field.memo_paragraphs.clone()));
                    }
                    Control::Table(t) => {
                        for cell in &t.cells {
                            walk(&cell.paragraphs, out);
                        }
                    }
                    _ => {}
                }
            }
        }
    }
    let mut memo_lists = Vec::new();
    walk(&section.paragraphs, &mut memo_lists);
    memo_lists
}
