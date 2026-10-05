// ==== find ====
                        let cs = tr.char_start.unwrap_or(0);
                        let cc = tr.text.chars().count();
                        if offset >= cs && offset <= cs + cc {
// ==== replace ====
                        // [claude-hwpx sel-skip-marker] 글머리표, 문단 번호 런은 char_start 가 None 이다(문서 글자가 아니다).
                        // 0번 글자로 셈하면 문단 처음 선택이 글머리표 앞에서 시작하고 끝이 글머리표 뒤에 걸렸다. 캐럿처럼 건너뛴다.
                        let cs = tr.char_start.unwrap_or(0);
                        let cc = tr.text.chars().count();
                        if tr.char_start.is_some() && offset >= cs && offset <= cs + cc {
