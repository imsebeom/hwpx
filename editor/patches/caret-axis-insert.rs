// ==== find ====
        let effective_char_offset = char_offset.min(text_len);
        let control_positions = self.control_text_positions();
        let inserts_before_inline_control = char_offset <= text_len
// ==== replace ====
        let effective_char_offset = char_offset.min(text_len);
        let control_positions = self.control_text_positions();
        // [claude-hwpx caret-axis] 캐럿이 글자처럼 취급 개체 바로 뒤면 같은 글자 위치의 개체 뒤에 넣는다.
        // 표지가 없으면 종전처럼 개체 앞에 넣는다(캐럿 축에서 그 자리를 가리킬 수 없던 결함).
        let after_inline = INSERT_AFTER_INLINE_CONTROLS.with(|flag| flag.get());
        // [claude-hwpx insert-after-count] 같은 글자 위치에 개체가 여럿이면 앞의 n 개 뒤, 나머지 앞에 넣는다.
        // 표지가 켜짐/꺼짐뿐이라 칸 안 두 그림 사이에 친 빈칸이 둘째 그림 뒤로 가 그림 사이가 벌어지지 않았다(2026-09-28).
        let claude_after_pos: Option<u32> = if after_inline && char_offset <= text_len && self.char_offsets.is_empty() {
            // 글 없는 문단은 개체 위치가 0, 1, ... 로 매겨지고 개체마다 8 칸씩 차례로 놓인다 — 개체 순서로 n 개 뒤
            let n = INSERT_AFTER_INLINE_COUNT.with(|c| c.get());
            let total_inline = self.controls.iter().filter(|c| c.is_logical_inline()).count();
            if n >= 1 && n < total_inline {
                let mut units = 0u32;
                let mut seen = 0usize;
                for c in &self.controls {
                    if seen == n {
                        break;
                    }
                    if c.occupies_ctrl_char_slot() {
                        units += 8;
                    }
                    if c.is_logical_inline() {
                        seen += 1;
                    }
                }
                Some(units)
            } else {
                None
            }
        } else if after_inline && char_offset <= text_len {
            let n = INSERT_AFTER_INLINE_COUNT.with(|c| c.get());
            let here: Vec<&Control> = self
                .controls
                .iter()
                .zip(control_positions.iter())
                .filter(|(_, &p)| p == effective_char_offset)
                .map(|(c, _)| c)
                .collect();
            let inline_here = here.iter().filter(|c| c.is_logical_inline()).count();
            if n >= 1 && n < inline_here {
                let base: u32 = if effective_char_offset == 0 {
                    0
                } else {
                    let i = effective_char_offset - 1;
                    self.char_offsets
                        .get(i)
                        .map(|&o| o + Self::char_stream_len(text_chars[i]))
                        .unwrap_or(0)
                };
                let mut units = 0u32;
                let mut seen = 0usize;
                for c in &here {
                    if seen == n {
                        break;
                    }
                    if c.occupies_ctrl_char_slot() {
                        units += 8;
                    }
                    if c.is_logical_inline() {
                        seen += 1;
                    }
                }
                Some(base + units)
            } else {
                None
            }
        } else {
            None
        };
        if claude_after_pos.is_none() && after_inline && char_offset <= text_len && effective_char_offset == text_len && !self.char_offsets.is_empty() {
            let trailing = control_positions.iter().filter(|&&pos| pos >= text_len).count();
            if trailing > 0 {
                return self.insert_text_at(text_len + trailing, new_text);
            }
        }
        let inserts_before_inline_control = !after_inline
            && char_offset <= text_len
