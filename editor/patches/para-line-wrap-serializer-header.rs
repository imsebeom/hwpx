// ==== find ====
            ("lineWrap", "BREAK"),
// ==== replace ====
            // [claude-hwpx para-line-wrap] 읽은 원문을 되쓴다(종전에는 늘 BREAK 라 「한 줄로 입력」이 저장에서 사라졌다)
            ("lineWrap", ps.hwpx_line_wrap.as_deref().unwrap_or("BREAK")),
