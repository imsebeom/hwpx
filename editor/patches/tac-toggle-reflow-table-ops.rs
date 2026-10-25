// ==== find ====
        if let Some(v) = json_bool(json, "treatAsChar") {
            if v {
// ==== replace ====
        // [claude-hwpx tac-toggle-reflow] 글자처럼 취급을 바꾸면 표를 담은 줄 높이가 달라진다 — 아래에서 그 문단을 다시 짠다
        let tac_changed = json_bool(json, "treatAsChar").is_some_and(|v| v != table.common.treat_as_char);
        if let Some(v) = json_bool(json, "treatAsChar") {
            if v {
// ==== next ====
        if (caption_created || caption_changed)
            && matches!(
                self.document.sections[section_idx].paragraphs[parent_para_idx].controls.get(control_idx),
                Some(crate::model::control::Control::Table(t)) if t.common.treat_as_char
            )
        {
// ==== replace ====
        // 글자처럼 취급을 켜거나 끈 표도 같다. 끈 뒤에는 표 높이만 한 옛 줄 높이가 남고, 그 뒤 칸 편집은 tac-host-sync 가
        // 글자처럼 취급 표만 맞춰 줄이 끝내 줄지 않았다(2026-10-25 「긴 글 → 글자처럼 취급 끄기 → 짧은 글」 에서 쪽이 줄지 않음)
        if tac_changed
            || (caption_created || caption_changed)
                && matches!(
                    self.document.sections[section_idx].paragraphs[parent_para_idx].controls.get(control_idx),
                    Some(crate::model::control::Control::Table(t)) if t.common.treat_as_char
                )
        {
