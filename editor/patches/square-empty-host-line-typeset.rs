// ==== find ====
                if has_picture_shape_square_wrap && runs_all_whitespace && !line_has_tac_control {
                    pairs.push((0.0, 0.0));
// ==== replace ====
                // [claude-hwpx square-empty-host-line] 글 없는 앵커 문단의 줄은 HWPX 에서 센다(d268 p4, d303: 한/글이 줄 높이 + 간격만큼 내려간다)
                let claude_empty_host = self.profile.get().hwpx_container() && para.text.trim().is_empty();
                if has_picture_shape_square_wrap && runs_all_whitespace && !line_has_tac_control && !claude_empty_host {
                    pairs.push((0.0, 0.0));
