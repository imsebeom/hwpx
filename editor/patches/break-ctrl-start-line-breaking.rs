// ==== find ====
fn char_index_to_utf16_offset(para: &Paragraph, char_index: usize) -> u32 {
// ==== replace ====
/// [claude-hwpx break-ctrl-start] 줄 시작의 UTF-16 위치 = 앞 줄 마지막 글자 바로 다음. 줄 경계의 조판 부호(하이퍼링크 시작 등)는 새 줄에 둔다
/// (한/글 2024 줄 기록, d309: 강제 줄바꿈 뒤 하이퍼링크 부호가 있으면 새 줄이 부호 위치에서 시작).
fn claude_line_start_utf16(para: &Paragraph, char_index: usize) -> u32 {
    let own = char_index_to_utf16_offset(para, char_index);
    if char_index > 0 {
        if let (Some(prev), Some(ch)) = (para.char_offsets.get(char_index - 1), para.text.chars().nth(char_index - 1)) {
            return (*prev + ch.len_utf16() as u32).min(own);
        }
    }
    own
}

fn char_index_to_utf16_offset(para: &Paragraph, char_index: usize) -> u32 {
// ==== next ====
                    } else {
                        char_index_to_utf16_offset(para, line.start_idx)
                    };
                    let text_end
// ==== replace ====
                    } else {
                        claude_line_start_utf16(para, line.start_idx)
                    };
                    let text_end
// ==== next ====
            0 // 첫 번째 줄의 text_start는 항상 0 (문단 시작)
        } else {
            char_index_to_utf16_offset(para, lb.start_idx)
// ==== replace ====
            0 // 첫 번째 줄의 text_start는 항상 0 (문단 시작)
        } else {
            claude_line_start_utf16(para, lb.start_idx)
// ==== next ====
                    text_start: if index == 0 {
                        0
                    } else {
                        char_index_to_utf16_offset(para, line.start_idx)
// ==== replace ====
                    text_start: if index == 0 {
                        0
                    } else {
                        claude_line_start_utf16(para, line.start_idx)
