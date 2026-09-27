    // [claude-hwpx caret-axis] 캐럿 축 복사. 문단들을 캐럿 범위로 잘라 내부 클립보드에 넣는다.
    fn copy_caret_paragraphs(
        &mut self,
        paragraphs: Vec<Paragraph>,
        start_caret: usize,
        end_caret: usize,
    ) -> Result<String, HwpError> {
        let last = paragraphs.len().saturating_sub(1);
        let mut clip_paragraphs: Vec<Paragraph> = paragraphs
            .iter()
            .enumerate()
            .map(|(i, para)| {
                let s = if i == 0 { start_caret } else { 0 };
                let e = if i == last { end_caret } else { usize::MAX };
                if s == 0 && e == usize::MAX {
                    para.clone()
                } else {
                    clip_paragraph_caret_range(para, s, e)
                }
            })
            .collect();
        for para in &mut clip_paragraphs {
            strip_structural_controls_for_text_clipboard(para);
        }
        let plain_text = clip_paragraphs
            .iter()
            .map(|para| para.text.as_str())
            .collect::<Vec<_>>()
            .join("\n");
        let escaped = super::super::helpers::json_escape(&plain_text);
        self.clipboard = Some(ClipboardData {
            paragraphs: clip_paragraphs,
            plain_text,
        });
        Ok(super::super::helpers::json_ok_with(&format!(
            "\"text\":\"{}\"",
            escaped
        )))
    }

    /// [claude-hwpx caret-axis] 본문 선택(캐럿 축)을 내부 클립보드에 복사한다.
    pub fn copy_selection_caret_native(
        &mut self,
        section_idx: usize,
        start_para_idx: usize,
        start_caret: usize,
        end_para_idx: usize,
        end_caret: usize,
    ) -> Result<String, HwpError> {
        let section = self
            .document
            .sections
            .get(section_idx)
            .ok_or_else(|| HwpError::RenderError(format!("구역 {} 범위 초과", section_idx)))?;
        if start_para_idx > end_para_idx || end_para_idx >= section.paragraphs.len() {
            return Err(HwpError::RenderError("문단 범위 오류".to_string()));
        }
        let paragraphs = section.paragraphs[start_para_idx..=end_para_idx].to_vec();
        self.copy_caret_paragraphs(paragraphs, start_caret, end_caret)
    }

    /// [claude-hwpx caret-axis] 셀 안 선택(캐럿 축)을 내부 클립보드에 복사한다.
    #[allow(clippy::too_many_arguments)]
    pub fn copy_selection_caret_in_cell_native(
        &mut self,
        section_idx: usize,
        parent_para_idx: usize,
        control_idx: usize,
        cell_idx: usize,
        start_cell_para_idx: usize,
        start_caret: usize,
        end_cell_para_idx: usize,
        end_caret: usize,
    ) -> Result<String, HwpError> {
        self.copy_selection_caret_in_cell_by_path_native(
            section_idx,
            parent_para_idx,
            &[(control_idx, cell_idx, start_cell_para_idx)],
            start_cell_para_idx,
            start_caret,
            end_cell_para_idx,
            end_caret,
        )
    }

    /// [claude-hwpx caret-axis] 경로가 가리키는 셀 안 선택(캐럿 축)을 내부 클립보드에 복사한다.
    #[allow(clippy::too_many_arguments)]
    pub fn copy_selection_caret_in_cell_by_path_native(
        &mut self,
        section_idx: usize,
        parent_para_idx: usize,
        path: &[(usize, usize, usize)],
        start_cell_para_idx: usize,
        start_caret: usize,
        end_cell_para_idx: usize,
        end_caret: usize,
    ) -> Result<String, HwpError> {
        if path.is_empty() || start_cell_para_idx > end_cell_para_idx {
            return Err(HwpError::RenderError("셀 선택 범위 오류".to_string()));
        }
        let mut paragraphs = Vec::new();
        for cell_para_idx in start_cell_para_idx..=end_cell_para_idx {
            let mut para_path = path.to_vec();
            para_path.last_mut().unwrap().2 = cell_para_idx;
            paragraphs.push(
                self.resolve_paragraph_by_path(section_idx, parent_para_idx, &para_path)?
                    .clone(),
            );
        }
        self.copy_caret_paragraphs(paragraphs, start_caret, end_caret)
    }

