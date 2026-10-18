// ==== find ====
fn format_search_hit(hit: &SearchHit, wrapped: bool) -> String {
// ==== replace ====
// [claude-hwpx footnote-search] 각주, 미주 안 글. 종전 검색은 본문, 칸, 글상자, 수식만 훑어 각주 안 글을 찾지도 바꾸지도 못했다(사용자 보고
// 2026-10-18). 각주가 달린 문단(본문, 또는 칸이면 cell 경로)과 그 문단 안 각주 컨트롤 번호, 각주 안 문단 번호로 가리킨다.
// anchor 는 각주가 달린 자리(캐럿 축)로, 스튜디오가 찾은 각주로 캐럿을 옮길 때 쓴다.
#[derive(Debug, Clone)]
struct ClaudeNoteHit {
    sec: usize,
    para: usize,
    cell: Option<CellHit>,
    ctrl: usize,
    inner: usize,
    char_offset: usize,
    length: usize,
    anchor: usize,
    endnote: bool,
}

#[allow(clippy::too_many_arguments)]
fn claude_note_hits_in(
    container: &crate::model::paragraph::Paragraph,
    sec: usize,
    para: usize,
    cell: Option<&CellHit>,
    query: &str,
    case_sensitive: bool,
    out: &mut Vec<ClaudeNoteHit>,
) {
    let qlen = query.chars().count();
    let mut anchors: Option<Vec<usize>> = None;
    for (ctrl, control) in container.controls.iter().enumerate() {
        let (paras, endnote) = match control {
            Control::Footnote(f) => (&f.paragraphs, false),
            Control::Endnote(e) => (&e.paragraphs, true),
            _ => continue,
        };
        for (inner, p) in paras.iter().enumerate() {
            for offset in find_in_text(&p.text, query, case_sensitive) {
                let anchor = anchors
                    .get_or_insert_with(|| crate::document_core::helpers::find_logical_control_positions(container))
                    .get(ctrl)
                    .copied()
                    .unwrap_or(0);
                out.push(ClaudeNoteHit {
                    sec,
                    para,
                    cell: cell.cloned(),
                    ctrl,
                    inner,
                    char_offset: offset,
                    length: qlen,
                    anchor,
                    endnote,
                });
            }
        }
    }
}

fn claude_note_hits_nested(
    container: &crate::model::paragraph::Paragraph,
    sec: usize,
    parent_para: usize,
    prefix: &mut Vec<(usize, usize, usize)>,
    query: &str,
    case_sensitive: bool,
    out: &mut Vec<ClaudeNoteHit>,
) {
    if prefix.len() >= MAX_NEST_DEPTH {
        return;
    }
    for (ctrl_idx, ctrl) in container.controls.iter().enumerate() {
        let groups: Vec<(usize, &[crate::model::paragraph::Paragraph])> = match ctrl {
            Control::Table(table) => table
                .cells
                .iter()
                .enumerate()
                .map(|(cell_idx, cell)| (cell_idx, cell.paragraphs.as_slice()))
                .collect(),
            Control::Shape(shape) => match get_textbox_from_shape(shape) {
                Some(tb) => vec![(0, tb.paragraphs.as_slice())],
                None => continue,
            },
            _ => continue,
        };
        for (cell_idx, paras) in groups {
            for (cell_para_idx, cell_para) in paras.iter().enumerate() {
                prefix.push((ctrl_idx, cell_idx, cell_para_idx));
                let hit = CellHit {
                    parent_para,
                    path: prefix.clone(),
                };
                claude_note_hits_in(cell_para, sec, parent_para, Some(&hit), query, case_sensitive, out);
                claude_note_hits_nested(cell_para, sec, parent_para, prefix, query, case_sensitive, out);
                prefix.pop();
            }
        }
    }
}

fn claude_search_notes(doc: &DocumentCore, query: &str, case_sensitive: bool) -> Vec<ClaudeNoteHit> {
    let mut out = Vec::new();
    if query.is_empty() {
        return out;
    }
    for (sec, section) in doc.document.sections.iter().enumerate() {
        for (para_idx, para) in section.paragraphs.iter().enumerate() {
            claude_note_hits_in(para, sec, para_idx, None, query, case_sensitive, &mut out);
            let mut prefix = Vec::new();
            claude_note_hits_nested(para, sec, para_idx, &mut prefix, query, case_sensitive, &mut out);
        }
    }
    out
}

impl DocumentCore {
    /// [claude-hwpx footnote-search] 각주, 미주 안 매치 목록(JSON 배열). index 는 replace_note_hit 에 넘기는 번호다.
    pub fn claude_search_note_text_native(&self, query: &str, case_sensitive: bool) -> String {
        let parts: Vec<String> = claude_search_notes(self, query, case_sensitive)
            .iter()
            .enumerate()
            .map(|(index, h)| {
                let cell = h.cell.as_ref().map(format_cell_context).unwrap_or_default();
                format!(
                    "{{\"index\":{},\"sec\":{},\"para\":{},\"noteCtrl\":{},\"notePara\":{},\"charOffset\":{},\"length\":{},\"anchorOffset\":{},\"endnote\":{}{}}}",
                    index, h.sec, h.para, h.ctrl, h.inner, h.char_offset, h.length, h.anchor, h.endnote, cell
                )
            })
            .collect();
        format!("[{}]", parts.join(","))
    }

    /// [claude-hwpx footnote-search] 각주, 미주 안 매치를 바꾼다(index 가 있으면 그 하나만). 바꾼 매치마다 구역 번호를 돌려준다.
    /// 바꾼 각주 문단은 각주 편집(reflow_footnote_paragraph)과 같은 폭(쪽 글 폭 - 문단 여백)으로 줄을 다시 만든다.
    fn claude_replace_note_hits(
        &mut self,
        query: &str,
        new_text: &str,
        case_sensitive: bool,
        index: Option<usize>,
    ) -> Result<Vec<usize>, HwpError> {
        let mut hits = claude_search_notes(self, query, case_sensitive);
        if let Some(n) = index {
            hits = hits.into_iter().nth(n).into_iter().collect();
        }
        hits.reverse();
        let dpi = self.dpi;
        let mut sections = Vec::new();
        for h in &hits {
            let section = self
                .document
                .sections
                .get_mut(h.sec)
                .ok_or_else(|| HwpError::RenderError("구역 범위 초과".into()))?;
            let page_def = &section.section_def.page_def;
            let text_width = crate::renderer::hwpunit_to_px(
                page_def.width as i32 - page_def.margin_left as i32 - page_def.margin_right as i32,
                dpi,
            );
            let host = match &h.cell {
                Some(cell) => Self::resolve_cell_paragraph_mut(section, cell.parent_para, &cell.path)?,
                None => section
                    .paragraphs
                    .get_mut(h.para)
                    .ok_or_else(|| HwpError::RenderError("문단 범위 초과".into()))?,
            };
            let note_para = match host.controls.get_mut(h.ctrl) {
                Some(Control::Footnote(f)) => f.paragraphs.get_mut(h.inner),
                Some(Control::Endnote(e)) => e.paragraphs.get_mut(h.inner),
                _ => None,
            }
            .ok_or_else(|| HwpError::RenderError("각주 검색 결과의 경로가 유효하지 않음".into()))?;
            note_para.delete_text_at(h.char_offset, h.length);
            note_para.insert_text_at(h.char_offset, new_text);
            let style = self.styles.para_styles.get(note_para.para_shape_id as usize);
            let width = (text_width
                - style.map(|s| s.margin_left).unwrap_or(0.0)
                - style.map(|s| s.margin_right).unwrap_or(0.0))
            .max(0.0);
            crate::renderer::composer::reflow_line_segs(
                note_para,
                crate::renderer::composer::ParagraphBox::content_width_px(width, dpi),
                &self.styles,
                dpi,
            );
            sections.push(h.sec);
        }
        Ok(sections)
    }

    /// [claude-hwpx footnote-search] 각주, 미주 안 index 번째 매치 하나를 바꾼다. 반환: {"ok":bool,"count":N}
    pub fn claude_replace_note_hit_native(
        &mut self,
        query: &str,
        new_text: &str,
        case_sensitive: bool,
        index: usize,
    ) -> Result<String, HwpError> {
        let mut sections = self.claude_replace_note_hits(query, new_text, case_sensitive, Some(index))?;
        let count = sections.len();
        sections.sort_unstable();
        sections.dedup();
        for sec_idx in sections {
            self.document.sections[sec_idx].raw_stream = None;
            self.recompose_section(sec_idx);
        }
        Ok(format!("{{\"ok\":{},\"count\":{}}}", count > 0, count))
    }
}

fn format_search_hit(hit: &SearchHit, wrapped: bool) -> String {
// ==== next ====
        // 변경된 섹션들 recompose
        if count > 0 {
// ==== replace ====
        // [claude-hwpx footnote-search] 모두 바꾸기(occurrence 없음)는 각주, 미주 안 글도 바꾼다
        if occurrence.is_none() {
            for sec in self.claude_replace_note_hits(query, new_text, case_sensitive, None)? {
                count += 1;
                affected_sections.push(sec);
            }
        }
        // 변경된 섹션들 recompose
        if count > 0 {
