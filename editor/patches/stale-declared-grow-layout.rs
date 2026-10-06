// ==== find ====
        if row_heights.is_empty() {
            return;
// ==== replace ====
        if row_heights.is_empty() {
            return;
        }
        // [claude-hwpx stale-declared-grow] 칸 문단에 줄 배치가 없으면 표 선언 높이는 지금 내용으로 잰 값이 아니다
        if crate::renderer::height_measurer::claude_declared_height_stale(table) {
            return;
