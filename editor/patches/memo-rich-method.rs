    /// [claude-hwpx memo-rich] 메모 본문의 글자 모양을 문단별 조각으로 돌려준다(패널이 그대로 그린다).
    /// [[{"t":"글","cs":글자모양번호,"bold":..,"italic":..,"underline":..,"strikethrough":..,"textColor":"#rrggbb"}]]
    pub fn get_memo_rich_json(&self, field_id: u32) -> Result<String, HwpError> {
        let mut items: Vec<ClaudeMemoItem> = Vec::new();
        for (si, sec) in self.document.sections.iter().enumerate() {
            claude_collect_memos(&sec.paragraphs, si, None, &[], &mut items);
        }
        let item = items
            .iter()
            .find(|it| it.field.field_id == field_id)
            .ok_or_else(|| HwpError::InvalidField("메모 필드를 찾지 못함".into()))?;
        let shapes = &self.document.doc_info.char_shapes;
        let run_json = |text: &str, id: u32| -> serde_json::Value {
            let mut v = serde_json::json!({ "t": text, "cs": id });
            if let Some(cs) = shapes.get(id as usize) {
                v["bold"] = cs.bold.into();
                v["italic"] = cs.italic.into();
                v["underline"] = (cs.underline_type != crate::model::style::UnderlineType::None).into();
                v["strikethrough"] = cs.strikethrough.into();
                v["textColor"] = crate::document_core::helpers::color_ref_to_css(cs.text_color).into();
            }
            v
        };
        let paras: Vec<serde_json::Value> = item
            .field
            .memo_paragraphs
            .iter()
            .map(|p| {
                let mut runs: Vec<serde_json::Value> = Vec::new();
                let mut cur = String::new();
                let mut cur_id: Option<u32> = None;
                for (i, ch) in p.text.chars().enumerate() {
                    let id = p.char_shape_id_at(i).unwrap_or(0);
                    if cur_id != Some(id) {
                        if let Some(prev) = cur_id {
                            runs.push(run_json(&cur, prev));
                        }
                        cur.clear();
                        cur_id = Some(id);
                    }
                    cur.push(ch);
                }
                if let Some(prev) = cur_id {
                    runs.push(run_json(&cur, prev));
                }
                serde_json::Value::Array(runs)
            })
            .collect();
        Ok(serde_json::Value::Array(paras).to_string())
    }

    /// [claude-hwpx memo-rich] 메모 본문을 글자 모양과 함께 바꾼다. 조각의 cs 를 바탕으로 굵게, 기울임, 밑줄, 취소선, 글자색을 얹는다.
    pub fn update_memo_rich(&mut self, field_id: u32, json: &str) -> Result<String, HwpError> {
        let paras: Vec<Vec<serde_json::Value>> =
            serde_json::from_str(json).map_err(|e| HwpError::InvalidField(e.to_string()))?;
        let text = |r: &serde_json::Value| r.get("t").and_then(|t| t.as_str()).unwrap_or("").to_string();
        let plain = paras
            .iter()
            .map(|p| p.iter().map(text).collect::<String>())
            .collect::<Vec<_>>()
            .join("\n");
        let base = {
            let mut items: Vec<ClaudeMemoItem> = Vec::new();
            for (si, sec) in self.document.sections.iter().enumerate() {
                claude_collect_memos(&sec.paragraphs, si, None, &[], &mut items);
            }
            items
                .iter()
                .find(|it| it.field.field_id == field_id)
                .and_then(|it| it.field.memo_paragraphs.first())
                .and_then(|p| p.char_shapes.first())
                .map(|c| c.char_shape_id)
                .unwrap_or(0)
        };
        let out = self.update_memo_body(field_id, &plain)?;
        let mut spans: Vec<(usize, usize, usize, u32)> = Vec::new();
        for (pi, runs) in paras.iter().enumerate() {
            let mut at = 0usize;
            for r in runs {
                let n = text(r).chars().count();
                let from = r.get("cs").and_then(|c| c.as_u64()).map(|c| c as u32).unwrap_or(base);
                let mods = crate::document_core::helpers::parse_char_shape_mods(&r.to_string());
                let id = self.document.find_or_create_char_shape(from, &mods);
                if n > 0 {
                    spans.push((pi, at, at + n, id));
                }
                at += n;
            }
        }
        let (s, root, path) = self.claude_memo_find(field_id)?;
        let start_pi = path.last().map(|h| h.2).unwrap_or(root);
        let hosts = if path.is_empty() {
            &mut self.document.sections[s].paragraphs
        } else {
            self.get_cell_paragraphs_mut_by_path(s, root, &path)?
        };
        let field = hosts
            .get_mut(start_pi)
            .and_then(|p| {
                p.controls.iter_mut().find_map(|c| match c {
                    Control::Field(f) if f.field_type == FieldType::Memo && f.field_id == field_id => Some(f),
                    _ => None,
                })
            })
            .ok_or_else(|| HwpError::InvalidField("메모 필드를 찾지 못함".into()))?;
        for (pi, a, b, id) in spans {
            if let Some(p) = field.memo_paragraphs.get_mut(pi) {
                p.apply_char_shape_range(a, b, id);
            }
        }
        Ok(out)
    }

