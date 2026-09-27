// ==== find ====
            Control::Table(table) if table.common.treat_as_char => Some(table.common.height as i32),
// ==== replace ====
            // [claude-hwpx tac-line-outer] 한글은 글자처럼 취급 표를 담은 줄 높이를 「표 높이 + 위아래 바깥 여백」으로 적는다
            // (본문 20385 + 141×2 = 20667, 칸 안 표 1282 + 283×2 = 1848). 여백을 빼면 표 옆 글을 고친 뒤 다시 나눈 줄이
            // 여백만큼 낮아져 표가 그만큼 줄었다(2026-09-28: 칸 안 머리표를 담은 문단을 고치자 바깥 표가 7.5px 줄었다).
            Control::Table(table) if table.common.treat_as_char => Some(
                table.common.height as i32
                    + table.outer_margin_top as i32
                    + table.outer_margin_bottom as i32,
            ),
