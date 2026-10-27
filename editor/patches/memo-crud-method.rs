    /// [claude-hwpx memo-crud] fieldId 로 메모를 찾는다: (구역, 본문 문단 또는 표를 품은 문단, 칸 경로).
    /// 경로 마지막 칸의 문단 번호가 메모가 시작하는 문단이다(경로가 비면 본문 문단 자체).
    fn claude_memo_find(&self, field_id: u32) -> Result<(usize, usize, Vec<(usize, usize, usize)>), HwpError> {
        let mut items: Vec<ClaudeMemoItem> = Vec::new();
        for (si, sec) in self.document.sections.iter().enumerate() {
            claude_collect_memos(&sec.paragraphs, si, None, &[], &mut items);
        }
        let hits: Vec<&ClaudeMemoItem> = items.iter().filter(|it| it.field.field_id == field_id).collect();
        match hits.as_slice() {
            [it] => Ok((it.section, it.root_para, it.hops.iter().map(|h| (h.control, h.cell, h.para)).collect())),
            [] => Err(HwpError::InvalidField(format!("메모 fieldId {} 없음", field_id))),
            _ => Err(HwpError::InvalidField(format!("fieldId {} 메모가 여럿", field_id))),
        }
    }

    /// [claude-hwpx memo-crud] 글자 k 앞의 표식 칸(8유닛) 하나를 뺀다. 글은 그대로 두고 그 뒤 위치만 8 당긴다.
    /// 칸이 없으면(위치표가 표식을 세지 않은 문단) 아무것도 안 한다.
    fn claude_memo_drop_gap(para: &mut Paragraph, k: usize) {
        let chars: Vec<char> = para.text.chars().collect();
        let k = k.min(chars.len());
        let size = |c: char| -> u32 { if c == '\t' { 8 } else { c.len_utf16() as u32 } };
        let prev_end = if k == 0 {
            0
        } else {
            para.char_offsets.get(k - 1).copied().unwrap_or(0) + size(chars[k - 1])
        };
        match para.char_offsets.get(k).copied() {
            Some(at) => {
                if at < prev_end + 8 {
                    return;
                }
                let lo = at - 8;
                for o in para.char_offsets.iter_mut().skip(k) {
                    *o -= 8;
                }
                for cs in para.char_shapes.iter_mut() {
                    if cs.start_pos >= at {
                        cs.start_pos -= 8;
                    } else if cs.start_pos > lo {
                        cs.start_pos = lo;
                    }
                }
                for ls in para.line_segs.iter_mut() {
                    if ls.text_start >= at {
                        ls.text_start -= 8;
                    } else if ls.text_start > lo {
                        ls.text_start = lo;
                    }
                }
            }
            None => {
                // 글 끝 뒤의 표식: 문단 끝 표식(1) 앞에 8칸이 남아 있어야 한다
                if para.char_count < prev_end + 8 + 1 {
                    return;
                }
            }
        }
        para.char_count -= 8;
    }

    /// [claude-hwpx memo-crud] 문단 목록에서 메모의 시작, 끝 표식과 필드 컨트롤을 걷는다. 걸린 글은 남는다.
    /// 끝 표식이 뒤 문단에 있으면(문단을 넘는 메모) 그 문단의 고아 끝 표식도 걷는다. 끝 문단 번호를 돌려준다.
    fn claude_memo_unwrap_in(paras: &mut [Paragraph], start_pi: usize, field_id: u32) -> Result<usize, HwpError> {
        let is_open = |p: &Paragraph, k: usize| -> Option<u32> {
            match p.controls.get(k) {
                Some(Control::Field(f)) if !p.field_ranges.iter().any(|r| r.control_idx == k) => Some(f.field_id),
                _ => None,
            }
        };
        let (ci, mut open) = {
            let para = paras
                .get_mut(start_pi)
                .ok_or_else(|| HwpError::InvalidField("메모 문단 위치 초과".into()))?;
            let ci = para
                .controls
                .iter()
                .position(|c| matches!(c, Control::Field(f) if f.field_type == FieldType::Memo && f.field_id == field_id))
                .ok_or_else(|| HwpError::InvalidField("메모 필드를 찾지 못함".into()))?;
            if let Some(ri) = para.field_ranges.iter().position(|r| r.control_idx == ci) {
                // 같은 문단에서 끝난다: 끝 표식은 end 글자 앞, 시작 표식은 start 글자 앞 칸
                let r = para.field_ranges.remove(ri);
                Self::claude_memo_drop_gap(para, r.end_char_idx);
                Self::claude_memo_drop_gap(para, r.start_char_idx);
                (ci, None)
            } else {
                // 뒤 문단에서 끝난다: 메모 목록(claude_collect_memos)과 같은 방식으로 끝 표식을 짝짓는다
                let at = para.control_text_positions().get(ci).copied().unwrap_or(para.text.chars().count());
                let open: Vec<u32> = (ci..para.controls.len()).filter_map(|k| is_open(para, k)).collect();
                Self::claude_memo_drop_gap(para, at);
                (ci, Some(open))
            }
        };
        let mut end_pi = start_pi;
        if let Some(open) = open.as_mut() {
            'walk: for pj in start_pi + 1..paras.len() {
                let p = &mut paras[pj];
                let mut hit = None;
                for (oi, o) in p.orphan_field_ends.iter().enumerate() {
                    let at = if o.begin_id_ref != 0 {
                        open.iter().rposition(|&id| id == o.begin_id_ref)
                    } else {
                        open.len().checked_sub(1)
                    };
                    let Some(at) = at else { continue };
                    if open.remove(at) == field_id {
                        hit = Some(oi);
                        break;
                    }
                }
                if let Some(oi) = hit {
                    let o = p.orphan_field_ends.remove(oi);
                    Self::claude_memo_drop_gap(p, o.char_idx);
                    p.invalidate_layout_inputs();
                    end_pi = pj;
                    break 'walk;
                }
                for k in 0..p.controls.len() {
                    if let Some(id) = is_open(p, k) {
                        open.push(id);
                    }
                }
            }
        }
        let para = &mut paras[start_pi];
        para.controls.remove(ci);
        if ci < para.ctrl_data_records.len() {
            para.ctrl_data_records.remove(ci);
        }
        for r in para.field_ranges.iter_mut() {
            if r.control_idx > ci {
                r.control_idx -= 1;
            }
        }
        para.invalidate_layout_inputs();
        Ok(end_pi)
    }

    /// [claude-hwpx memo-crud] 메모를 지운다(한/글 「메모 지우기」). 걸린 글은 그대로 두고 메모 표식과 본문만 걷는다.
    pub fn delete_memo(&mut self, field_id: u32) -> Result<String, HwpError> {
        let (s, root, path) = self.claude_memo_find(field_id)?;
        if path.is_empty() {
            let stored_end_for_reset = crate::renderer::composer::paragraph_flow_end(
                &self.document.sections[s].paragraphs[root],
            );
            let section = &mut self.document.sections[s];
            section.raw_stream = None;
            let end_pi = Self::claude_memo_unwrap_in(&mut section.paragraphs, root, field_id)?;
            for pi in root..=end_pi {
                self.reflow_paragraph(s, pi);
            }
            let doc_hwp3_layout = self.document.layout_profile().hwp3_layout();
            crate::renderer::composer::recalculate_section_vpos(
                &mut self.document.sections[s].paragraphs,
                root,
                None,
                stored_end_for_reset,
                &self.styles,
                self.dpi,
                doc_hwp3_layout,
            );
            for pi in root..=end_pi {
                self.recompose_paragraph(s, pi);
            }
        } else {
            let start_pi = path.last().map(|h| h.2).unwrap_or(0);
            let end_pi = {
                let paras = self.get_cell_paragraphs_mut_by_path(s, root, &path)?;
                Self::claude_memo_unwrap_in(paras, start_pi, field_id)?
            };
            for pi in start_pi..=end_pi {
                let mut p = path.clone();
                if let Some(last) = p.last_mut() {
                    last.2 = pi;
                }
                self.reflow_cell_paragraph_by_path(s, root, &p, pi);
            }
            self.recalculate_cell_paragraph_vpos_by_path(s, root, &path, start_pi, None);
            self.mark_cell_control_dirty(s, root, path[0].0);
            if let Some(section) = self.document.sections.get_mut(s) {
                section.raw_stream = None;
            }
            self.mark_section_dirty(s);
        }
        self.paginate_if_needed();
        self.invalidate_page_tree_cache();
        Ok(format!("{{\"ok\":true,\"fieldId\":{}}}", field_id))
    }

    /// [claude-hwpx memo-crud] 메모 본문을 바꾼다. 줄마다 문단 하나이고 서식은 옛 첫 문단을 물려받는다.
    /// 작성자와 작성 일시는 그대로 둔다. 본문은 조판에 들지 않으므로 다시 조판하지 않는다.
    pub fn update_memo_body(&mut self, field_id: u32, body: &str) -> Result<String, HwpError> {
        let (s, root, path) = self.claude_memo_find(field_id)?;
        let start_pi = path.last().map(|h| h.2).unwrap_or(root);
        let paras = if path.is_empty() {
            &mut self.document.sections[s].paragraphs
        } else {
            self.get_cell_paragraphs_mut_by_path(s, root, &path)?
        };
        let field = paras
            .get_mut(start_pi)
            .and_then(|p| {
                p.controls.iter_mut().find_map(|c| match c {
                    Control::Field(f) if f.field_type == FieldType::Memo && f.field_id == field_id => Some(f),
                    _ => None,
                })
            })
            .ok_or_else(|| HwpError::InvalidField("메모 필드를 찾지 못함".into()))?;
        let template = field.memo_paragraphs.first().cloned();
        field.memo_paragraphs = body
            .split('\n')
            .map(|line| {
                let line = line.strip_suffix('\r').unwrap_or(line);
                let mut p = match &template {
                    Some(t) => Paragraph::new_empty_like(t),
                    None => Paragraph::new_empty(),
                };
                if !line.is_empty() {
                    p.insert_text_at(0, line);
                }
                p
            })
            .collect();
        if !path.is_empty() {
            self.mark_cell_control_dirty(s, root, path[0].0);
        }
        if let Some(section) = self.document.sections.get_mut(s) {
            section.raw_stream = None;
        }
        self.mark_section_dirty(s);
        Ok(format!("{{\"ok\":true,\"fieldId\":{}}}", field_id))
    }

