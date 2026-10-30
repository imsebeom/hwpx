// ==== find ====
    claude_attach_memo_lists(&records, &mut section.paragraphs);
// ==== replace ====
    claude_attach_memo_lists(&records, &mut section.paragraphs);
    // [claude-hwpx memo-tail-root] 구역 끝 메모 목록을 품는 빈 문단은 본문이 아니다. 저장 때 serialize_memo_tail 이 다시 만든다.
    // 남겨 두면 저장하고 열 때마다 본문 문단이 하나씩 는다(276 → 277, 2026-10-30)
    if let Some(last) = records.iter().rposition(|r| r.tag_id == tags::HWPTAG_PARA_HEADER && r.level == 0) {
        let holds_memo_list = records[last..].iter().any(|r| r.tag_id == tags::HWPTAG_MEMO_LIST);
        let empty = section.paragraphs.last().is_some_and(|p| p.text.is_empty() && p.controls.is_empty());
        if holds_memo_list && empty && section.paragraphs.len() > 1 {
            section.paragraphs.pop();
        }
    }
