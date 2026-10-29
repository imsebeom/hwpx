// ==== find ====
        if crate::renderer::height_measurer::claude_declared_height_stale(table) {
            return;
        }
// ==== replace ====
        if crate::renderer::height_measurer::claude_declared_height_stale(table) {
            return;
        }
        // [claude-hwpx tac-no-shrink-hwpx] HWPX 글자처럼 취급 표는 선언 높이로 행을 키우지도 않는다(측정과 같은 규칙). 에디터 저장본은
        // 선언이 옛 엔진 값이라 마지막 행이 그만큼 커졌다(결과보고서 161번 표: 선언 67717, 내용 66755 → 마지막 행 +12.8px)
        if table.common.treat_as_char && self.profile.get().hwpx_container() {
            return;
        }
// ==== next ====
                            let include_trailing_ls = !is_cell_last_line
                                || (para_count > 1 && table.common.treat_as_char);
// ==== replace ====
                            // [claude-hwpx tac-no-shrink-hwpx] HWPX 는 여러 문단 칸도 마지막 줄 뒤 간격 제외(측정과 같은 회계)
                            let include_trailing_ls = !is_cell_last_line
                                || (para_count > 1
                                    && table.common.treat_as_char
                                    && (self.profile.get().native_hwp5_layout() || self.profile.get().hwp3_layout()));
