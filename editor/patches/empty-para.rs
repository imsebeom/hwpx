// ==== find ====
                }
            }
            Ok(Event::Eof) => break,
            Err(e) => return Err(HwpxError::XmlError(format!("section: {}", e))),
// ==== replace ====
                }
            }
            // [claude-hwpx empty-para] 스스로 닫힌 빈 문단
            Ok(Event::Empty(ref e)) if local_name(e.name().as_ref()) == b"p" => {
                section.paragraphs.push(claude_parse_empty_paragraph(e)?.0);
            }
            Ok(Event::Eof) => break,
            Err(e) => return Err(HwpxError::XmlError(format!("section: {}", e))),
// ==== next ====
    Ok(section)
}
// ==== replace ====
    Ok(section)
}

/// [claude-hwpx empty-para] 스스로 닫힌 `<hp:p .../>` 를 빈 문단으로 읽는다.
///
/// 한/글은 이것을 빈 문단 하나로 연다(다시 저장하면 `<hp:p ...><hp:linesegarray>…` 로 나온다). 종전에는 시작 태그만
/// 문단으로 받아 이런 문단이 통째로 사라졌다 — 삽화 삽입 스크립트가 만든 그림 문단 뒤 빈 줄이 없어져 아래 표가 한 줄
/// 위로 올라갔다(2026-10-06 한국문화 14단원 마지막 쪽). 속성은 그대로 두고 닫는 태그를 붙여 보통 문단처럼 읽는다.
fn claude_parse_empty_paragraph(
    e: &quick_xml::events::BytesStart,
) -> Result<(Paragraph, Option<SectionDef>), HwpxError> {
    let head: String = AsRef::<str>::as_ref(e).to_owned();
    let name: String = AsRef::<str>::as_ref(&e.name()).to_owned();
    let xml = format!("<{head}></{name}>");
    let mut reader = Reader::from_str(&xml);
    let mut buf = Vec::new();
    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(ref s)) => return parse_paragraph(s, &mut reader),
            Ok(Event::Eof) => return Ok((Paragraph::default(), None)),
            Err(err) => return Err(HwpxError::XmlError(format!("empty p: {}", err))),
            _ => {}
        }
        buf.clear();
    }
}
// ==== next ====
                        root_sub_list_seen = true;
                    }
                    _ => {}
                }
// ==== replace ====
                        root_sub_list_seen = true;
                    }
                    // [claude-hwpx empty-para]
                    b"p" => master_page.paragraphs.push(claude_parse_empty_paragraph(e)?.0),
                    _ => {}
                }
// ==== next ====
                parse_caption_sub_list_attrs(ce, &mut caption);
            }
            Ok(Event::End(ref end)) => {
                if local_name(end.name().as_ref()) == b"caption" {
// ==== replace ====
                parse_caption_sub_list_attrs(ce, &mut caption);
            }
            // [claude-hwpx empty-para]
            Ok(Event::Empty(ref ce)) if local_name(ce.name().as_ref()) == b"p" => {
                caption.paragraphs.push(claude_parse_empty_paragraph(ce)?.0);
            }
            Ok(Event::End(ref end)) => {
                if local_name(end.name().as_ref()) == b"caption" {
// ==== next ====
            Ok(Event::Empty(ref ce)) => {
                let cname = ce.name();
                let local = local_name(cname.as_ref());
                match local {
                    b"cellAddr" => {
                        for attr in ce.attributes().flatten() {
                            match attr.key.as_ref().as_bytes() {
                                b"colAddr" => {
// ==== replace ====
            Ok(Event::Empty(ref ce)) => {
                let cname = ce.name();
                let local = local_name(cname.as_ref());
                match local {
                    // [claude-hwpx empty-para]
                    b"p" => cell.paragraphs.push(claude_parse_empty_paragraph(ce)?.0),
                    b"cellAddr" => {
                        for attr in ce.attributes().flatten() {
                            match attr.key.as_ref().as_bytes() {
                                b"colAddr" => {
// ==== next ====
                    }
                    b"textMargin" => {
// ==== replace ====
                    }
                    // [claude-hwpx empty-para] 삼키지는 않되 빈 문단으로는 남긴다(한/글과 같게)
                    b"p" => text_box.paragraphs.push(claude_parse_empty_paragraph(ce)?.0),
                    b"textMargin" => {
// ==== next ====
                    paragraphs.push(para);
                }
            }
            Ok(Event::End(ref ee)) => {
                let eename = ee.name();
                if local_name(eename.as_ref()) == end_tag {
// ==== replace ====
                    paragraphs.push(para);
                }
            }
            // [claude-hwpx empty-para]
            Ok(Event::Empty(ref ce)) if local_name(ce.name().as_ref()) == b"p" => {
                paragraphs.push(claude_parse_empty_paragraph(ce)?.0);
            }
            Ok(Event::End(ref ee)) => {
                let eename = ee.name();
                if local_name(eename.as_ref()) == end_tag {
// ==== next ====
                    root_sub_list_seen = true;
                }
// ==== replace ====
                    root_sub_list_seen = true;
                } else if local == b"p" {
                    // [claude-hwpx empty-para]
                    layout.paragraphs.push(claude_parse_empty_paragraph(ce)?.0);
                }
