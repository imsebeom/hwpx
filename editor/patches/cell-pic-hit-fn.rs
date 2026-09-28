    /// [claude-hwpx cell-pic-hit] 글 없이 글자처럼 취급 그림만 있는 칸 문단을 눌렀을 때의 자리와 캐럿 x.
    /// 이런 줄에는 빈 글자 조각 하나만 있어, 클릭 판정이 어디를 눌러도 그 조각(첫 그림 안쪽)에 붙어 위치 0 과
    /// 엉뚱한 x 를 돌려줬다(2026-09-28: 두 그림 사이, 둘째 그림 오른쪽을 눌러도 캐럿이 첫 그림 가운데쯤에 섰다).
    /// 그림 사이 자리(0..=개체 수)마다 claude_cell_inline_caret 로 x 를 구해 클릭 x 에 가장 가까운 자리를 고른다.
    pub(crate) fn claude_cell_pic_hit(
        &self,
        section_idx: usize,
        parent_para_idx: usize,
        control_idx: usize,
        cell_idx: usize,
        cell_para_idx: usize,
        x: f64,
    ) -> Option<(usize, f64)> {
        let para = match self
            .document
            .sections
            .get(section_idx)?
            .paragraphs
            .get(parent_para_idx)?
            .controls
            .get(control_idx)?
        {
            Control::Table(t) => t.cells.get(cell_idx)?.paragraphs.get(cell_para_idx)?,
            _ => return None,
        };
        if !para.text.trim().is_empty()
            || !para
                .controls
                .iter()
                .any(|c| matches!(c, Control::Picture(p) if p.common.treat_as_char))
        {
            return None;
        }
        let slots = para.controls.iter().filter(|c| c.is_logical_inline()).count();
        let mut best: Option<(usize, f64)> = None;
        for off in 0..=slots {
            let Ok((Some(json), _)) = self.claude_cell_inline_caret(
                section_idx,
                parent_para_idx,
                control_idx,
                cell_idx,
                cell_para_idx,
                off,
            ) else {
                continue;
            };
            let Some(cx) = serde_json::from_str::<serde_json::Value>(&json)
                .ok()
                .and_then(|v| v.get("x").and_then(|x| x.as_f64()))
            else {
                continue;
            };
            if best.map_or(true, |(_, bx)| (cx - x).abs() < (bx - x).abs()) {
                best = Some((off, cx));
            }
        }
        best
    }

    /// [claude-hwpx cell-pic-hit] 클릭 결과 JSON 의 cursorRect.x 만 바꾼다(그림 가장자리 x).
    pub(crate) fn claude_hit_with_x(hit: String, x: f64) -> String {
        match serde_json::from_str::<serde_json::Value>(&hit) {
            Ok(mut v) => {
                if let Some(r) = v.get_mut("cursorRect") {
                    r["x"] = serde_json::json!((x * 10.0).round() / 10.0);
                }
                v.to_string()
            }
            Err(_) => hit,
        }
    }

