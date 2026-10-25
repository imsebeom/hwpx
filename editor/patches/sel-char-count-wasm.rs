// ==== find ====
    #[wasm_bindgen(js_name = getTextInCellByPath)]
// ==== replace ====
    /// [claude-hwpx sel-char-count] 고른 범위의 글자 수 `[공란 포함, 공란 제외]`(스튜디오 플러그인 selection-count 의 상태 표시줄).
    /// 위치는 에디터 캐럿 축이다(글자와 글자처럼 취급하는 개체가 한 칸, 각주와 미주는 칸이 아님). `parent_para_idx` 가 음수면 본문,
    /// 아니면 `path_json` 칸(글상자)의 문단이다. 범위 안에 놓인 표 칸, 글상자, 묶음, 캡션 글도 세고 각주, 미주 글과 문단 끝은 세지 않는다.
    /// 공란은 빈칸, 탭 같은 공백 문자다. `end_off` 가 문단 길이 이상이면 문단 끝에 붙은 개체까지 넣는다
    #[wasm_bindgen(js_name = claudeSelectionCharCount)]
    pub fn claude_selection_char_count(
        &self,
        section_idx: u32,
        parent_para_idx: i32,
        path_json: &str,
        start_para: u32,
        start_off: u32,
        end_para: u32,
        end_off: u32,
    ) -> Result<String, JsValue> {
        type N = (usize, usize);
        fn is_note(c: &Control) -> bool {
            matches!(c, Control::Footnote(_) | Control::Endnote(_))
        }
        fn paras(ps: &[Paragraph], n: &mut N) {
            for p in ps {
                para(p, 0, usize::MAX, n);
            }
        }
        fn caption(c: &Option<crate::model::shape::Caption>, n: &mut N) {
            if let Some(c) = c {
                paras(&c.paragraphs, n);
            }
        }
        fn shape(s: &ShapeObject, n: &mut N) {
            match s {
                ShapeObject::Group(g) => {
                    for c in &g.children {
                        shape(c, n);
                    }
                    caption(&g.caption, n);
                }
                ShapeObject::Picture(p) => caption(&p.caption, n),
                _ => {
                    if let Some(tb) = crate::document_core::helpers::get_textbox_from_shape(s) {
                        paras(&tb.paragraphs, n);
                    }
                }
            }
        }
        fn control(c: &Control, n: &mut N) {
            match c {
                Control::Table(t) => {
                    for cell in &t.cells {
                        paras(&cell.paragraphs, n);
                    }
                    caption(&t.caption, n);
                }
                Control::Shape(s) => shape(s, n),
                Control::Picture(p) => caption(&p.caption, n),
                _ => {}
            }
        }
        // 컨트롤은 자기 글자 위치의 글자 앞에 온다(control_text_positions 규약)
        fn para(p: &Paragraph, from: usize, to: usize, n: &mut N) {
            let chars: Vec<char> = p.text.chars().collect();
            let positions = p.control_text_positions();
            let mut at: Vec<Vec<usize>> = vec![Vec::new(); chars.len() + 1];
            for ci in 0..p.controls.len() {
                at[positions.get(ci).copied().unwrap_or(chars.len()).min(chars.len())].push(ci);
            }
            let slot = |ci: usize| p.controls[ci].is_logical_inline() && !is_note(&p.controls[ci]);
            let caret_len = chars.len() + (0..p.controls.len()).filter(|&ci| slot(ci)).count();
            let mut c = 0usize;
            for (i, ctrls) in at.iter().enumerate() {
                for &ci in ctrls {
                    let ctrl = &p.controls[ci];
                    let s = slot(ci);
                    let inside = c >= from && (c < to || (!s && to >= caret_len));
                    if inside && !is_note(ctrl) {
                        control(ctrl, n);
                    }
                    c += s as usize;
                }
                if let Some(&ch) = chars.get(i) {
                    if c >= from && c < to && ch != '\n' && ch != '\r' {
                        n.0 += 1;
                        n.1 += !ch.is_whitespace() as usize;
                    }
                    c += 1;
                }
            }
        }
        let sec = section_idx as usize;
        let mut path = if parent_para_idx < 0 { Vec::new() } else { DocumentCore::parse_cell_path(path_json)? };
        let mut n: N = (0, 0);
        for p in start_para..=end_para {
            let target = if parent_para_idx < 0 {
                self.document
                    .sections
                    .get(sec)
                    .and_then(|s| s.paragraphs.get(p as usize))
                    .ok_or_else(|| JsValue::from_str("문단 번호가 범위 밖이다"))?
            } else {
                if let Some(last) = path.last_mut() {
                    last.2 = p as usize;
                }
                self.resolve_paragraph_by_path(sec, parent_para_idx as usize, &path)?
            };
            let from = if p == start_para { start_off as usize } else { 0 };
            let to = if p == end_para { end_off as usize } else { usize::MAX };
            para(target, from, to, &mut n);
        }
        Ok(format!("[{},{}]", n.0, n.1))
    }

    #[wasm_bindgen(js_name = getTextInCellByPath)]
