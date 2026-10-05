// ==== find ====
            let char_start = text_run.char_start.unwrap_or(0);
            let char_count = effective_char_count(text_run);

            if offset >= char_start && offset <= char_start + char_count {
// ==== replace ====
            // [claude-hwpx cell-caret-skip-marker] 글머리표, 문단 번호 런(char_start: None)은 문서 글자가 아니다.
            // 0번 글자로 셈하면 칸 안 글머리표 문단의 0~2번 캐럿이 글머리표 위에 그려져 실제 위치와 어긋났다(본문 캐럿은 건너뛴다).
            let char_start = text_run.char_start.unwrap_or(0);
            let char_count = effective_char_count(text_run);

            if text_run.char_start.is_some() && offset >= char_start && offset <= char_start + char_count {
// ==== next ====
                    let cs = tr.char_start.unwrap_or(0);
                    let cc = effective_char_count(tr);
                    if offset >= cs && offset <= cs + cc {
// ==== replace ====
                    let cs = tr.char_start.unwrap_or(0);
                    let cc = effective_char_count(tr);
                    if tr.char_start.is_some() && offset >= cs && offset <= cs + cc {
