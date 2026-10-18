// ==== find ====
    /// 각주 문단 리플로우
    pub(crate) fn reflow_footnote_paragraph(
// ==== replace ====
    /// [claude-hwpx fn-char-format] 각주, 미주 문단의 글자 위치 글자 모양을 JSON 으로 돌려준다(머리말 판과 같은 형식).
    pub fn claude_get_char_properties_in_footnote_native(
        &self,
        section_idx: usize,
        para_idx: usize,
        control_idx: usize,
        fn_para_idx: usize,
        char_offset: usize,
    ) -> Result<String, HwpError> {
        let paragraph = self
            .get_footnote_paragraph_ref(section_idx, para_idx, control_idx, fn_para_idx)
            .ok_or_else(|| HwpError::RenderError("각주 문단을 찾을 수 없음".to_string()))?;
        let offset = char_offset.min(paragraph.text.chars().count());
        Ok(self.build_char_properties_json(paragraph, offset))
    }

    /// [claude-hwpx fn-char-format] 각주, 미주 문단 범위에 글자 모양을 적용한다. 범위 안 run 마다 그 모양에 바꾼 속성만 더한다.
    #[allow(clippy::too_many_arguments)]
    pub fn claude_apply_char_format_in_footnote_native(
        &mut self,
        section_idx: usize,
        para_idx: usize,
        control_idx: usize,
        start_fn_para: usize,
        start_offset: usize,
        end_fn_para: usize,
        end_offset: usize,
        props_json: &str,
    ) -> Result<String, HwpError> {
        if (start_fn_para, start_offset) > (end_fn_para, end_offset) {
            return Err(HwpError::RenderError("시작 위치가 끝 위치보다 뒤에 있음".to_string()));
        }
        let mut mods = crate::document_core::helpers::parse_char_shape_mods(props_json);
        if json_has_border_keys(props_json) {
            mods.border_fill_id = Some(self.create_border_fill_from_json(props_json));
        }
        let mut changed = Vec::new();
        for fp in start_fn_para..=end_fn_para {
            // 범위 안 글자마다 지금 모양을 읽어 같은 모양끼리 묶는다
            let runs: Vec<(usize, usize, u32)> = {
                let p = self
                    .get_footnote_paragraph_ref(section_idx, para_idx, control_idx, fp)
                    .ok_or_else(|| HwpError::RenderError("각주 문단을 찾을 수 없음".to_string()))?;
                let len = p.text.chars().count();
                let a = if fp == start_fn_para { start_offset.min(len) } else { 0 };
                let b = if fp == end_fn_para { end_offset.min(len) } else { len };
                let mut runs: Vec<(usize, usize, u32)> = Vec::new();
                for i in a..b {
                    let id = p.char_shape_id_at(i).unwrap_or(0);
                    match runs.last_mut() {
                        Some(last) if last.2 == id && last.1 == i => last.1 = i + 1,
                        _ => runs.push((i, i + 1, id)),
                    }
                }
                runs
            };
            if runs.is_empty() {
                continue;
            }
            for (x, y, base) in runs {
                let new_id = self.document.find_or_create_char_shape(base, &mods);
                self.get_footnote_paragraph_mut(section_idx, para_idx, control_idx, fp)?
                    .apply_char_shape_range(x, y, new_id);
            }
            changed.push(fp);
        }
        if changed.is_empty() {
            return Ok("{\"ok\":true,\"changed\":0}".to_string());
        }
        self.rebuild_resolved_styles();
        for fp in &changed {
            self.reflow_footnote_paragraph(section_idx, para_idx, control_idx, *fp);
        }
        self.document.sections[section_idx].raw_stream = None;
        self.mark_section_dirty(section_idx);
        self.paginate_if_needed();
        self.invalidate_page_tree_cache();
        Ok(format!("{{\"ok\":true,\"changed\":{}}}", changed.len()))
    }

    /// 각주 문단 리플로우
    pub(crate) fn reflow_footnote_paragraph(
