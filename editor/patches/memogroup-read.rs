// ==== find ====
pub fn parse_hwpx_section(xml: &str) -> Result<Section, HwpxError> {
    let mut section = Section::default();
// ==== replace ====
pub fn parse_hwpx_section(xml: &str) -> Result<Section, HwpxError> {
    let mut section = Section::default();
    // [claude-hwpx memogroup-read] python-hwpx 가 구역 끝에 쓰는 메모 묶음(메모 id, 본문 문단)
    let mut claude_memo_bodies: Vec<(String, Vec<Paragraph>)> = Vec::new();
// ==== next ====
                    b"p" => {
                        // 최상위 문단
                        let (para, sec_def_opt) = parse_paragraph(e, &mut reader)?;
                        if let Some(sec_def) = sec_def_opt {
                            section.section_def = sec_def;
                        }
                        section.paragraphs.push(para);
                    }
// ==== replace ====
                    b"p" => {
                        // 최상위 문단
                        let (para, sec_def_opt) = parse_paragraph(e, &mut reader)?;
                        if let Some(sec_def) = sec_def_opt {
                            section.section_def = sec_def;
                        }
                        section.paragraphs.push(para);
                    }
                    b"memogroup" => {
                        claude_parse_memogroup(&mut reader, &mut claude_memo_bodies)?;
                    }
// ==== next ====
    link_orphan_field_ends(&mut section.paragraphs);

    Ok(section)
}
// ==== replace ====
    claude_attach_memogroup(&mut section.paragraphs, &claude_memo_bodies);
    link_orphan_field_ends(&mut section.paragraphs);

    Ok(section)
}

/// python-hwpx(`add_memo_with_anchor`)가 쓰는 메모 묶음을 읽는다.
///
/// 한/글은 메모 본문을 `fieldBegin type="MEMO"` 안 subList 에 적는다. python-hwpx 는 본문을 구역 끝의
/// `<hp:memogroup><hp:memo id><hp:paraList>` 에 따로 두고, 필드 subList 에는 그 메모 id 만 글로 적는다.
/// 종전에는 이 묶음의 문단이 본문 문단으로 읽혀 문서 끝에 메모 글이 본문처럼 나타났고 메모와는 이어지지 않았다.
/// 한/글 2024 는 이 묶음을 읽지 않는다(메모 풍선에 id 숫자가 보이고, 다시 저장하면 묶음이 사라진다 — 2026-10-06 실측).
/// 여기서는 묶음의 본문을 같은 id 의 메모 필드에 붙인다. 그러면 저장할 때 한/글 모양(subList 에 본문)으로 나간다.
fn claude_parse_memogroup(
    reader: &mut Reader<&[u8]>,
    bodies: &mut Vec<(String, Vec<Paragraph>)>,
) -> Result<(), HwpxError> {
    let mut buf = Vec::new();
    let mut memo_id = String::new();
    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(ref ce)) => {
                let cname = ce.name();
                match local_name(cname.as_ref()) {
                    b"memo" => {
                        memo_id.clear();
                        for attr in ce.attributes().flatten() {
                            if attr.key.as_ref().as_bytes() == b"id" {
                                memo_id = attr_str(&attr);
                            }
                        }
                    }
                    b"paraList" => {
                        let paragraphs = parse_sublist_paragraphs(reader, b"paraList")?;
                        bodies.push((memo_id.clone(), paragraphs));
                    }
                    _ => {}
                }
            }
            Ok(Event::End(ref ee)) => {
                let eename = ee.name();
                if local_name(eename.as_ref()) == b"memogroup" {
                    break;
                }
            }
            Ok(Event::Eof) => break,
            Err(e) => return Err(HwpxError::XmlError(format!("memogroup: {}", e))),
            _ => {}
        }
        buf.clear();
    }
    Ok(())
}

/// 메모 묶음의 본문을 `ID` 매개변수가 같은 메모 필드에 붙인다(python-hwpx 는 본문 문단에만 메모를 건다).
fn claude_attach_memogroup(paragraphs: &mut [Paragraph], bodies: &[(String, Vec<Paragraph>)]) {
    if bodies.is_empty() {
        return;
    }
    for para in paragraphs.iter_mut() {
        for control in para.controls.iter_mut() {
            let Control::Field(field) = control else {
                continue;
            };
            if field.field_type != FieldType::Memo {
                continue;
            }
            let body = field.parameters.items.iter().find_map(|p| match p {
                crate::model::control::Parameter::String {
                    name: Some(name),
                    value,
                    ..
                } if name == "ID" => bodies.iter().find(|(memo_id, _)| memo_id == value),
                _ => None,
            });
            if let Some((_, body)) = body {
                field.memo_paragraphs = body.clone();
            }
        }
    }
}
