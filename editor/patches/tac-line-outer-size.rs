// ==== find ====
            let width = table.flow_width_hu() as i32;
            (width, table.common.height as i32)
// ==== replace ====
            let width = table.flow_width_hu() as i32;
            // [claude-hwpx tac-line-outer-size] 줄 높이에 쓰이므로 위아래 바깥 여백을 더한다(tac-line-outer 와 같은 까닭).
            // 개체만 있는 빈 문단은 이 값으로 줄을 만든다 — 칸 안 표 옆 글을 지워 문단이 비면 줄이 1848 → 1282 로 줄었다.
            (
                width,
                table.common.height as i32
                    + table.outer_margin_top as i32
                    + table.outer_margin_bottom as i32,
            )
