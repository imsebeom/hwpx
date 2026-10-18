// ==== find ====
        // 배경/테두리 렌더링을 위한 시작 위치 기록
        // 문단 경계 = 이전 문단 끝 = y_start (spacing_before 적용 전)
// ==== replace ====
        // [claude-hwpx bullet-place] 글머리표 표식 자리는 글자 폭이 아니라 한/글 규칙(표식 칸 + 본문과의 거리, 줄 나눔과 같은 값)이다.
        // 이어지는 줄은 자동 내어쓰기일 때만 그만큼 민다(끄면 들여쓰기만). 자동 내어쓰기 + 양수 들여쓰기는 종전대로
        let claude_bullet: Option<(f64, bool)> = para.and_then(|p| {
            let (advance, auto) = crate::renderer::composer::claude_bullet_head_hwp(p, styles)?;
            let indent = styles
                .para_styles
                .get(p.para_shape_id as usize)
                .map(|s| s.indent)
                .unwrap_or(0.0);
            (advance > 0 && !(auto && indent > 0.0)).then(|| (hwpunit_to_px(advance, self.dpi), auto))
        });
        let numbering_width = match claude_bullet {
            Some((advance, _)) if numbering_width > 0.0 => advance,
            _ => numbering_width,
        };
        let claude_cont_offset = match claude_bullet {
            Some((advance, true)) => advance,
            Some((_, false)) => 0.0,
            None => numbering_width,
        };

        // 배경/테두리 렌더링을 위한 시작 위치 기록
        // 문단 경계 = 이전 문단 끝 = y_start (spacing_before 적용 전)
// ==== next ====
            // 번호/글머리표 마커: 모든 줄에서 마커 폭만큼 가용폭 차감 (행잉 인덴트)
            let num_offset = if numbering_width > 0.0 {
                numbering_width
            } else {
                0.0
            };
// ==== replace ====
            // 번호/글머리표 마커: 모든 줄에서 마커 폭만큼 가용폭 차감 (행잉 인덴트)
            // [claude-hwpx bullet-place] 첫 줄은 표식 자리, 이어지는 줄은 내어쓰기 몫(글머리표는 자동 내어쓰기일 때만)
            let num_offset = if line_idx == start_line && start_line == 0 {
                numbering_width
            } else {
                claude_cont_offset
            };
// ==== next ====
                    line_node.children.push(num_node);
                    x += num_width;
// ==== replace ====
                    line_node.children.push(num_node);
                    // [claude-hwpx bullet-place] 글머리표는 그린 글자 폭이 아니라 표식 자리만큼 나아간다
                    x += if claude_bullet.is_some() { numbering_width } else { num_width };
