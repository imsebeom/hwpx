// ==== find ====
            if cursor_line == 0
                && end_line > cursor_line + 1
                && end_line < line_count
                && next_para_is_rowbreak_anchor_table
// ==== replace ====
            if cursor_line == 0
                && end_line > cursor_line + 1
                && end_line < line_count
                && next_para_is_rowbreak_anchor_table
                // [claude-hwpx no-anchor-line-back] HWPX 는 한 줄을 되돌리지 않는다(d075 6쪽: 한/글 2줄 | 1줄)
                && !st.profile.hwpx_container()
