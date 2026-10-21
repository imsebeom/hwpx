    /// [claude-hwpx memo-new] 문단 안 [start, end) 글에 메모(한/글 검토 메모)를 건다. path 가 비면 본문 문단, 있으면 셀 문단.
    /// 걸린 글은 그대로 두고 MEMO 필드의 시작과 끝 표식만 넣는다. 본문은 줄마다 문단 하나다.
    /// 형식은 한/글 2024 저장본을 따른다: 매개변수 7종(Command `MEMO/65535/<번호>/<id>/<id>/<작성자>/\;;`, ID `memo<번호>`,
    /// Number, Author, MemoShapeIDRef 65535, CreateDateTime), zorder = 번호(memo-zorder 패치가 memo_index 로 쓴다).
    /// Command 의 두 id 는 작성 시각 FILETIME(UTC)의 하위, 상위 32비트다. 한/글은 날짜를 여기서 읽고 CreateDateTime 은
    /// 그 시각을 현지 시각으로 적는다(2026-10-21 실측: 둘 다 1 이면 한/글 저장본이 1601-01-01T09:07:09Z).
    pub fn insert_memo_at(
        &mut self,
        section_idx: usize,
        parent_para_idx: usize,
        path: &[(usize, usize, usize)],
        start: usize,
        end: usize,
        author: &str,
        body: &str,
        created: &str,
        file_time: (u32, u32),
    ) -> Result<String, HwpError> {
        // 번호: 문서 메모 번호의 최댓값 + 1
        let mut items: Vec<ClaudeMemoItem> = Vec::new();
        for (si, sec) in self.document.sections.iter().enumerate() {
            claude_collect_memos(&sec.paragraphs, si, None, &[], &mut items);
        }
        let number = items
            .iter()
            .map(|it| {
                if it.field.memo_index > 0 {
                    it.field.memo_index
                } else {
                    it.field.command.split('/').nth(2).and_then(|t| t.parse::<u32>().ok()).unwrap_or(0)
                }
            })
            .max()
            .unwrap_or(0)
            + 1;
        let field_id = self.next_click_here_field_id();
        let esc = |s: &str| s.replace('&', "&amp;").replace('<', "&lt;").replace('>', "&gt;");
        let command = format!("MEMO/65535/{}/{}/{}/{}/\\;;", number, file_time.0, file_time.1, author);
        let params_xml = format!(
            concat!(
                r#"<hp:parameters cnt="7" name="">"#,
                r#"<hp:integerParam name="Prop">0</hp:integerParam>"#,
                r#"<hp:stringParam name="Command">{}</hp:stringParam>"#,
                r#"<hp:stringParam name="ID">memo{}</hp:stringParam>"#,
                r#"<hp:integerParam name="Number">{}</hp:integerParam>"#,
                r#"<hp:stringParam name="Author">{}</hp:stringParam>"#,
                r#"<hp:stringParam name="MemoShapeIDRef">65535</hp:stringParam>"#,
                r#"<hp:stringParam name="CreateDateTime">{}</hp:stringParam>"#,
                r#"</hp:parameters>"#,
            ),
            esc(&command),
            number,
            number,
            esc(author),
            esc(created),
        );
        let memo_paragraphs: Vec<Paragraph> = body
            .split('\n')
            .map(|line| {
                let mut p = Paragraph::new_empty();
                if !line.is_empty() {
                    p.insert_text_at(0, line);
                }
                p
            })
            .collect();
        let wrap = |para: &mut Paragraph| -> Result<(usize, usize), HwpError> {
            let len = para.text.chars().count();
            let (s, e) = (start.min(len), end.min(len).max(start.min(len)));
            insert_field_with_text_in_para(
                para,
                s,
                field_id,
                FieldType::Memo,
                tags::FIELD_MEMO,
                command.clone(),
                1 | (1 << 15),
                &params_xml,
                "",
            )?;
            // 빈 글을 넣었으니 범위는 한 점이다 — 걸 글의 끝까지 늘리고 메모 내용을 채운다
            let ctrl_idx = para
                .controls
                .iter()
                .position(|c| matches!(c, Control::Field(f) if f.field_id == field_id))
                .ok_or_else(|| HwpError::InvalidField("새 메모 필드를 찾지 못함".into()))?;
            for r in &mut para.field_ranges {
                if r.control_idx == ctrl_idx {
                    r.end_char_idx = e;
                }
            }
            if let Control::Field(f) = &mut para.controls[ctrl_idx] {
                f.memo_index = number;
                // 매개변수 트리도 채운다 — getMemoList 가 작성자와 시각을 여기서 읽는다(파일을 다시 열면 파서가 채우는 값)
                f.parameters = crate::model::control::ParameterList::parse_xml(&params_xml).unwrap_or_default();
                f.memo_paragraphs = memo_paragraphs.clone();
            }
            Ok((s, e))
        };
        let (s, e) = if path.is_empty() {
            let section = self
                .document
                .sections
                .get_mut(section_idx)
                .ok_or_else(|| HwpError::InvalidField("구역 인덱스 초과".into()))?;
            section.raw_stream = None;
            let para = section
                .paragraphs
                .get_mut(parent_para_idx)
                .ok_or_else(|| HwpError::InvalidField("문단 인덱스 초과".into()))?;
            wrap(para)?
        } else {
            wrap(self.get_cell_paragraph_mut_by_path(section_idx, parent_para_idx, path)?)?
        };
        if path.is_empty() {
            let stored_end_for_reset = crate::renderer::composer::paragraph_flow_end(
                &self.document.sections[section_idx].paragraphs[parent_para_idx],
            );
            self.reflow_paragraph(section_idx, parent_para_idx);
            let doc_hwp3_layout = self.document.layout_profile().hwp3_layout();
            crate::renderer::composer::recalculate_section_vpos(
                &mut self.document.sections[section_idx].paragraphs,
                parent_para_idx,
                None,
                stored_end_for_reset,
                &self.styles,
                self.dpi,
                doc_hwp3_layout,
            );
            self.recompose_paragraph(section_idx, parent_para_idx);
        } else {
            let outer_ctrl = path[0].0;
            let inner_para = path.last().map(|entry| entry.2).unwrap_or(0);
            self.reflow_cell_paragraph_by_path(section_idx, parent_para_idx, path, inner_para);
            self.recalculate_cell_paragraph_vpos_by_path(section_idx, parent_para_idx, path, inner_para, None);
            self.mark_cell_control_dirty(section_idx, parent_para_idx, outer_ctrl);
            if let Some(section) = self.document.sections.get_mut(section_idx) {
                section.raw_stream = None;
            }
            self.mark_section_dirty(section_idx);
        }
        self.paginate_if_needed();
        self.invalidate_page_tree_cache();
        Ok(format!(
            "{{\"ok\":true,\"fieldId\":{},\"number\":{},\"start\":{},\"end\":{}}}",
            field_id, number, s, e
        ))
    }

