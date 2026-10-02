// ==== find ====
            let trailing_ls_hu = if vpos_continuous && prev_has_text {
// ==== replace ====
            // [claude-hwpx lazy-base-empty-bridge] 저장 위치가 이어지면(이 문단 시작 = 앞 문단 끝) 앞이 빈 문단이어도 줄 간격 다리를 놓지 않는다.
            // 빈 문단의 줄 간격도 화면 누적 y 에 이미 들어 있어(빈 문단 21.3px = 13.3 + 8) 다리를 놓으면 기준이 600 작아지고, 뒤 문단이
            // 저장 위치로 8px 씩 밀려 쪽 끝 줄이 넘쳤다(2026-10-02 260927 판 칸 Enter 뒤 3쪽 끝 소제목 9.7px, 쪽 나누기는 붙이지 않는다)
            // 미주 흐름(suppress_large_forward_jump)은 빈 간격 문단의 줄 간격에 미주 사이 간격을 실어 두므로 종전대로 다리를 놓는다.
            // 화면 그리기에만 적용한다(col_area_y > 0 — 쪽 나누기 커서는 단 위치 0 에서 센다). 쪽 나누기까지 바꾸면 문서 300개 중 5개의
            // 쪽 배치가 흔들렸다(넷은 한/글 쪽으로, 둘은 반대로). 화면이 쪽 나누기와 같은 기준을 쓰게 하는 것이 이 보정의 목적이다
            let claude_render_cursor = self.col_area_y > 0.5;
            let trailing_ls_hu = if vpos_continuous
                && (prev_has_text || (!self.suppress_large_forward_jump && claude_render_cursor))
            {
