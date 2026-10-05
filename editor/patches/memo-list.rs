// ==== find ====
    /// getFieldList: 모든 필드를 JSON 배열로 반환
// ==== replace ====
    /// [claude-hwpx memo-list] 문서의 메모를 JSON 배열로 돌려준다(에디터의 메모 패널, cli memos).
    ///
    /// `getFieldList` 는 메모 본문, 작성자, 작성 일시를 내주지 않고, 걸린 글이 문단을 넘는 메모는 빠뜨린다
    /// (FieldRange 는 한 문단 안의 범위만 적는다 — 표 많은 문서에서 메모 23개 중 10개가 빠졌다).
    /// 여기서는 필드 컨트롤을 직접 걸으며 다음 문단들의 끝 표식(orphan_field_ends)과 짝짓는다.
    /// 위치는 캐럿 축이다(스튜디오 커서, 선택 영역 사각형 API 와 같은 축).
    /// `paraIndex` 는 본문 문단(칸 안이면 표를 품은 문단), `path` 는 칸 경로(마지막 칸의 문단이 시작 문단),
    /// `startPara`/`endPara` 는 걸린 글이 든 문단 목록 안에서의 문단 번호다.
    pub fn get_memo_list_json(&self) -> String {
        let mut items: Vec<ClaudeMemoItem> = Vec::new();
        for (si, sec) in self.document.sections.iter().enumerate() {
            claude_collect_memos(&sec.paragraphs, si, None, &[], &mut items);
        }
        let entries: Vec<String> = items.iter().map(claude_memo_json).collect();
        format!("[{}]", entries.join(","))
    }

    /// getFieldList: 모든 필드를 JSON 배열로 반환
// ==== next ====
/// 문단에서 필드를 수집한다 (재귀: 표 셀, 글상자 내부 포함).
fn collect_fields_from_paragraph(
// ==== replace ====
/// [claude-hwpx memo-list] 메모가 있는 문단 목록까지 내려가는 한 단계(표 칸 또는 글상자).
#[derive(Clone)]
struct ClaudeMemoHop {
    textbox: bool,
    control: usize,
    cell: usize,
    para: usize,
}

/// 메모 하나: 필드와 걸린 글의 범위(캐럿 축).
struct ClaudeMemoItem<'a> {
    field: &'a Field,
    section: usize,
    root_para: usize,
    hops: Vec<ClaudeMemoHop>,
    start_para: usize,
    start: usize,
    end_para: usize,
    end: usize,
    /// 끝 표식을 찾았는가. 못 찾았으면 범위는 시작 자리 한 점이다.
    closed: bool,
    anchor: String,
}

/// 문단 목록에서 (문단, 글자) 두 자리 사이의 글. 문단 사이는 줄바꿈으로 잇는다.
fn claude_memo_span_text(
    paras: &[Paragraph],
    from_para: usize,
    from_char: usize,
    to_para: usize,
    to_char: usize,
) -> String {
    let mut out = String::new();
    for pi in from_para..=to_para {
        let Some(para) = paras.get(pi) else { break };
        let chars: Vec<char> = para.text.chars().collect();
        let a = if pi == from_para { from_char.min(chars.len()) } else { 0 };
        let b = if pi == to_para { to_char.min(chars.len()) } else { chars.len() };
        if pi > from_para {
            out.push('\n');
        }
        if a < b {
            out.extend(&chars[a..b]);
        }
    }
    out
}

/// 한 문단 목록(본문, 칸, 글상자)의 메모를 모으고 그 안의 표와 글상자로 내려간다.
fn claude_collect_memos<'a>(
    paras: &'a [Paragraph],
    section: usize,
    root_para: Option<usize>,
    hops: &[ClaudeMemoHop],
    out: &mut Vec<ClaudeMemoItem<'a>>,
) {
    // 이 목록 안에서 열린 채 다음 문단으로 넘어간 필드: (필드 id, 메모면 out 번호, 시작 문단, 시작 글자)
    let mut open: Vec<(u32, Option<usize>, usize, usize)> = Vec::new();
    for (pi, para) in paras.iter().enumerate() {
        let inline_upto = |count: usize| {
            para.controls
                .iter()
                .take(count)
                .filter(|ctrl| ctrl.is_logical_inline())
                .count()
        };
        // 앞 문단에서 시작한 필드의 끝 표식
        for orphan in &para.orphan_field_ends {
            let at = if orphan.begin_id_ref != 0 {
                open.iter().rposition(|entry| entry.0 == orphan.begin_id_ref)
            } else {
                open.len().checked_sub(1)
            };
            let Some(at) = at else { continue };
            let (_, memo, start_para, start_char) = open.remove(at);
            if let Some(mi) = memo {
                let item = &mut out[mi];
                item.end_para = pi;
                item.end =
                    crate::document_core::helpers::text_to_logical_offset(para, orphan.char_idx);
                item.closed = true;
                item.anchor =
                    claude_memo_span_text(paras, start_para, start_char, pi, orphan.char_idx);
            }
        }
        let text_len = para.text.chars().count();
        let positions = para.control_text_positions();
        for (ci, ctrl) in para.controls.iter().enumerate() {
            let Control::Field(field) = ctrl else { continue };
            let is_memo = field.field_type == FieldType::Memo;
            let range = para.field_ranges.iter().find(|r| r.control_idx == ci);
            if range.is_some() && !is_memo {
                continue;
            }
            let mut here = hops.to_vec();
            if let Some(last) = here.last_mut() {
                last.para = pi;
            }
            let new_item = |start: usize, end: usize, closed: bool, anchor: String| ClaudeMemoItem {
                field,
                section,
                root_para: root_para.unwrap_or(pi),
                hops: here.clone(),
                start_para: pi,
                start,
                end_para: pi,
                end,
                closed,
                anchor,
            };
            match range {
                Some(r) => {
                    // 같은 문단에서 끝난다. 사이에 든 글자처럼 취급 개체(표, 그림)도 범위에 넣는다
                    let start = r.start_char_idx.min(text_len) + inline_upto(ci);
                    let end =
                        r.end_char_idx.min(text_len) + inline_upto(ci + 1 + r.inner_slot_count);
                    let anchor =
                        claude_memo_span_text(paras, pi, r.start_char_idx, pi, r.end_char_idx);
                    out.push(new_item(start, end.max(start), true, anchor));
                }
                None => {
                    let start_char = positions.get(ci).copied().unwrap_or(text_len).min(text_len);
                    let memo = if is_memo {
                        let start = start_char + inline_upto(ci);
                        out.push(new_item(start, start, false, String::new()));
                        Some(out.len() - 1)
                    } else {
                        None
                    };
                    open.push((field.field_id, memo, pi, start_char));
                }
            }
        }
        for (ci, ctrl) in para.controls.iter().enumerate() {
            let mut next = hops.to_vec();
            if let Some(last) = next.last_mut() {
                last.para = pi;
            }
            let root = Some(root_para.unwrap_or(pi));
            match ctrl {
                Control::Table(table) => {
                    for (cell_i, cell) in table.cells.iter().enumerate() {
                        let mut path = next.clone();
                        path.push(ClaudeMemoHop {
                            textbox: false,
                            control: ci,
                            cell: cell_i,
                            para: 0,
                        });
                        claude_collect_memos(&cell.paragraphs, section, root, &path, out);
                    }
                }
                Control::Shape(shape) => {
                    for (node, paragraphs) in shape_lists(shape) {
                        let mut path = next.clone();
                        path.push(ClaudeMemoHop {
                            textbox: true,
                            control: ci,
                            cell: node,
                            para: 0,
                        });
                        claude_collect_memos(paragraphs, section, root, &path, out);
                    }
                }
                _ => {}
            }
        }
    }
}

fn claude_memo_json(item: &ClaudeMemoItem) -> String {
    let field = item.field;
    let param = |key: &str| -> String {
        field
            .parameters
            .items
            .iter()
            .find_map(|p| match p {
                crate::model::control::Parameter::String {
                    name: Some(name),
                    value,
                    ..
                } if name == key => Some(value.clone()),
                _ => None,
            })
            .unwrap_or_default()
    };
    let body: Vec<&str> = field
        .memo_paragraphs
        .iter()
        .map(|p| p.text.as_str())
        .collect();
    let path: Vec<String> = item
        .hops
        .iter()
        .map(|h| {
            format!(
                "{{\"controlIndex\":{},\"cellIndex\":{},\"cellParaIndex\":{},\"textbox\":{}}}",
                h.control, h.cell, h.para, h.textbox
            )
        })
        .collect();
    format!(
        "{{\"fieldId\":{},\"number\":{},\"author\":{},\"createdAt\":{},\"command\":{},\"text\":{},\"anchor\":{},\"sectionIndex\":{},\"paraIndex\":{},\"path\":[{}],\"startPara\":{},\"startOffset\":{},\"endPara\":{},\"endOffset\":{},\"closed\":{}}}",
        field.field_id,
        field.memo_index,
        json_escape(&param("Author")),
        json_escape(&param("CreateDateTime")),
        json_escape(&field.command),
        json_escape(&body.join("\n")),
        json_escape(&item.anchor),
        item.section,
        item.root_para,
        path.join(","),
        item.start_para,
        item.start,
        item.end_para,
        item.end,
        item.closed,
    )
}

/// 문단에서 필드를 수집한다 (재귀: 표 셀, 글상자 내부 포함).
fn collect_fields_from_paragraph(
