// ==== find ====
                                    let will_render_inline =
                                        composed.tac_controls.iter().any(|&(abs_pos, _, ci)| {
                                            ci == ctrl_idx
                                                && composed.lines.iter().any(|line| {
                                                    let line_chars: usize = line
                                                        .runs
                                                        .iter()
                                                        .map(|r| r.text.chars().count())
                                                        .sum();
                                                    abs_pos >= line.char_start
                                                        && abs_pos < line.char_start + line_chars
                                                })
                                        });
// ==== replace ====
                                    // [claude-hwpx cell-pic-split-dup] 쪽을 넘는 칸에서 문단 끝(마지막 글자 다음)의
                                    // 글자처럼 취급 그림은 abs_pos == line_chars 라 위 판정에 빠져 칸 왼쪽에 한 번 더
                                    // 그려졌다. 나뉘지 않은 표(table_layout.rs, Task #928)처럼 줄 안에 그려 등록된
                                    // 자리가 있는지로 판정한다. rhwp devel d5fbe8b5d(#7171)의 수정과 같다 — v0.8.6 이후
                                    // 릴리스로 올리면 이 패치를 걷는다
                                    let will_render_inline = tree
                                        .get_inline_shape_position(
                                            section_index,
                                            cp_idx,
                                            ctrl_idx,
                                            Some(&cell_context),
                                        )
                                        .is_some();
                                    // 문단이 쪽 경계에서 갈라져 그림 줄이 이 조각에 없으면(start_line..end_line 밖)
                                    // 그 줄을 가진 조각이 그린다 — 여기서 그리면 앞 조각 칸 왼쪽에 또 나온다.
                                    // devel 에도 남아 있는 경우다
                                    let will_render_inline = will_render_inline
                                        || (!all_runs_empty
                                            && composed.tac_controls.iter().any(
                                                |&(abs_pos, _, ci)| {
                                                    let line = composed
                                                        .lines
                                                        .iter()
                                                        .rposition(|l| l.char_start <= abs_pos)
                                                        .unwrap_or(0);
                                                    ci == ctrl_idx
                                                        && (line < start_line || line >= end_line)
                                                },
                                            ));
