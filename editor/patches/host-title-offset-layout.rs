// ==== find ====
                let table_y_start = if is_current_visible_para_float
                    && signed_hwpunit(t.common.vertical_offset) > 0
                {
                    let host_line_px = para
// ==== replace ====
                let table_y_start = if is_current_visible_para_float
                    && signed_hwpunit(t.common.vertical_offset) > 0
                    // [claude-hwpx host-title-offset] HWPX 는 오프셋이 첫 줄 높이보다 작으면 글줄이 표 아래로 간다(사본 실험 경계 1299/1300)
                    && !(self.profile.get().hwpx_container()
                        && para.line_segs.first().is_some_and(|s| {
                            signed_hwpunit(t.common.vertical_offset) < s.line_height
                        }))
                {
                    let host_line_px = para
// ==== next ====
                y_offset = if is_current_visible_para_float {
                    let mut flow_y = if signed_hwpunit(t.common.vertical_offset) > 0 {
// ==== replace ====
                y_offset = if is_current_visible_para_float {
                    // [claude-hwpx host-title-offset] 오프셋이 첫 줄 높이보다 작으면 글줄이 표 아래로 가므로 흐름도 표 바닥에서 잇는다(오프셋 0 분기)
                    let claude_text_below_table = self.profile.get().hwpx_container()
                        && para.line_segs.first().is_some_and(|s| {
                            signed_hwpunit(t.common.vertical_offset) < s.line_height
                        });
                    let mut flow_y = if signed_hwpunit(t.common.vertical_offset) > 0
                        && !claude_text_below_table
                    {
