// [claude-hwpx caret-axis] 캐럿 축과 다른 두 축을 오가는 도우미.
//
// 스튜디오의 캐럿 위치(DocumentPosition.charOffset)는 **캐럿 축**이다 — 글자 하나, 글자처럼
// 취급하는 개체(표, 그림, 수식, 도형) 하나, 각주와 미주 하나를 각각 한 칸으로 센다
// (`Control::is_logical_inline`, `navigable_text_len`, 렌더 트리의 `char_start`).
// 문단 모델에는 축이 둘 더 있다.
//   - 글자 축: `para.text` 의 글자 번호. `insert_text_at`, `delete_text_at`, 복사 자르기가 쓴다.
//   - 나누기 축: 글자 + `Paragraph::is_split_movable_control` 컨트롤. `split_at` 이 쓴다.
// 스튜디오가 캐럿 위치를 글자 축 함수에 그대로 넘겨, 글자처럼 취급하는 개체 뒤에서는 입력,
// 삭제, 복사, 선택 음영이 한 칸씩 어긋났고 개체 자체는 선택 범위에 들어가도 지워지거나
// 복사되지 않았다.

/// 문단의 글자와 컨트롤을 문서 순서로 늘어놓는다: (컨트롤 번호, 캐럿 칸 여부, 나누기 칸 여부).
/// 컨트롤은 자기 글자 위치의 글자보다 앞에 온다(`control_text_positions` 규약).
fn caret_axis_items(para: &Paragraph) -> Vec<(Option<usize>, bool, bool)> {
    let text_len = para.text.chars().count();
    let positions = para.control_text_positions();
    let mut at: Vec<Vec<usize>> = vec![Vec::new(); text_len + 1];
    for ci in 0..para.controls.len() {
        let pos = positions.get(ci).copied().unwrap_or(text_len).min(text_len);
        at[pos].push(ci);
    }
    let mut items = Vec::with_capacity(text_len + para.controls.len());
    for (i, ctrls) in at.iter().enumerate() {
        for &ci in ctrls {
            let ctrl = &para.controls[ci];
            items.push((
                Some(ci),
                ctrl.is_logical_inline(),
                Paragraph::is_split_movable_control(ctrl),
            ));
        }
        if i < text_len {
            items.push((None, true, true));
        }
    }
    items
}

/// 캐럿 축 → 나누기 축. 캐럿 칸 `caret` 개를 지난 바로 그 자리(뒤따르는 캐럿 밖 컨트롤 앞)다.
pub(crate) fn caret_to_split_offset(para: &Paragraph, caret: usize) -> usize {
    let (mut c, mut s) = (0usize, 0usize);
    for (_, is_caret, is_split) in caret_axis_items(para) {
        if c >= caret {
            break;
        }
        c += is_caret as usize;
        s += is_split as usize;
    }
    s
}

/// 나누기 축 → 캐럿 축.
pub(crate) fn split_to_caret_offset(para: &Paragraph, split: usize) -> usize {
    let (mut c, mut s) = (0usize, 0usize);
    for (_, is_caret, is_split) in caret_axis_items(para) {
        if s >= split {
            break;
        }
        c += is_caret as usize;
        s += is_split as usize;
    }
    c
}

/// 컨트롤마다 캐럿 칸 번호. 캐럿 칸을 차지하지 않는 컨트롤은 None.
pub(crate) fn caret_control_slots(para: &Paragraph) -> Vec<Option<usize>> {
    let mut slots = vec![None; para.controls.len()];
    let mut c = 0usize;
    for (ci, is_caret, _) in caret_axis_items(para) {
        if let (Some(ci), true) = (ci, is_caret) {
            slots[ci] = Some(c);
        }
        c += is_caret as usize;
    }
    slots
}

/// 컨트롤마다 PARA_TEXT 안 UTF-16 시작 위치(8 코드 유닛 갭). `delete_control_native_impl`,
/// 직렬화기와 같은 규칙으로 갭을 컨트롤 순서대로 배정한다.
pub(crate) fn control_utf16_positions(para: &Paragraph) -> Vec<u32> {
    let text_chars: Vec<char> = para.text.chars().collect();
    let mut result = Vec::with_capacity(para.controls.len());
    let mut prev_end: u32 = 0;
    for (i, ch) in text_chars.iter().enumerate() {
        let offset = para.char_offsets.get(i).copied().unwrap_or(prev_end);
        while prev_end + 8 <= offset && result.len() < para.controls.len() {
            result.push(prev_end);
            prev_end += 8;
        }
        let size: u32 = if *ch == '\t' {
            8
        } else if ch.len_utf16() == 2 {
            2
        } else {
            1
        };
        prev_end = offset + size;
    }
    while result.len() < para.controls.len() {
        result.push(prev_end);
        prev_end += 8;
    }
    result
}

/// UTF-16 위치(줄 시작 `text_start` 등) → 캐럿 축. 그 위치 앞의 글자 수 + 캐럿 칸 컨트롤 수.
pub(crate) fn utf16_pos_to_caret_idx(para: &Paragraph, utf16_pos: u32) -> usize {
    let chars_before = utf16_pos_to_char_idx(&para.char_offsets, utf16_pos);
    let ctrls_before = control_utf16_positions(para)
        .iter()
        .zip(para.controls.iter())
        .filter(|(pos, ctrl)| **pos < utf16_pos && ctrl.is_logical_inline())
        .count();
    chars_before + ctrls_before
}

/// 캐럿 축 위치에 글을 넣는다(캐럿이 개체 바로 뒤면 개체 뒤에). 넣은 자리의 글자 축 위치를 돌려준다.
/// 붙여넣기의 한 문단 경로가 쓴다 — 여러 문단 경로(`split_at`)는 원래 캐럿 축과 맞았다.
pub(crate) fn insert_text_at_caret(para: &mut Paragraph, caret: usize, text: &str) -> usize {
    let (text_offset, after_inline) = logical_to_text_offset(para, caret);
    crate::model::paragraph::INSERT_AFTER_INLINE_CONTROLS.with(|flag| flag.set(after_inline));
    let n = crate::model::paragraph::claude_inline_before_at(para, caret, text_offset);
    crate::model::paragraph::INSERT_AFTER_INLINE_COUNT.with(|c| c.set(n));
    para.insert_text_at(text_offset, text);
    crate::model::paragraph::INSERT_AFTER_INLINE_COUNT.with(|c| c.set(usize::MAX));
    crate::model::paragraph::INSERT_AFTER_INLINE_CONTROLS.with(|flag| flag.set(false));
    text_offset
}

