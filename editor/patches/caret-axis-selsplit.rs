// ==== find ====
                expected_segments += 1;

                let cursor_pair = tree_cache.iter().find_map(|(pn, tree)| {
// ==== replace ====
                expected_segments += 1;

                // [claude-hwpx caret-axis] 캐럿 칸 개체(글자처럼 취급 표, 그림, 수식, 각주)가 있는 문단은 여기서 칠한다.
                // 렌더 트리의 글자 조각은 글자 축 번호를 쓰므로 캐럿 축 범위를 그대로 넘기면 개체 뒤에서 한 칸씩
                // 밀렸고, 표나 그림이 든 줄은 줄 정보 한 줄이 화면 여러 행(앞 글 / 개체 / 뒤 글)으로 그려져 한
                // 사각형으로 칠할 수 없었다. 개체 자리에서 나눠 글 조각은 글자 축 캐럿으로, 개체는 상자로 칠한다.
                {
                    let slots = crate::document_core::helpers::caret_control_slots(para);
                    if slots.iter().any(|slot| slot.is_some()) {
                        let mut blocks: Vec<(usize, usize)> = slots
                            .iter()
                            .enumerate()
                            .filter_map(|(ci, slot)| {
                                let slot = (*slot)?;
                                (slot >= range_start && slot < range_end).then_some((slot, ci))
                            })
                            .collect();
                        blocks.sort_unstable();
                        let mut pieces: Vec<(usize, usize, Option<usize>)> = Vec::new();
                        let mut cur = range_start;
                        for &(slot, ci) in &blocks {
                            if cur < slot {
                                pieces.push((cur, slot, None));
                            }
                            pieces.push((slot, slot + 1, Some(ci)));
                            cur = slot + 1;
                        }
                        if cur < range_end {
                            pieces.push((cur, range_end, None));
                        }
                        let mut hit_piece = false;
                        for (a, b, ctrl) in pieces {
                            for (pn, tree) in &tree_cache {
                                let rect = match ctrl {
                                    Some(ci) => caret_axis_find_control_box(
                                        &tree.root,
                                        section_idx,
                                        para_idx,
                                        ci,
                                        cell_target,
                                    ),
                                    None => {
                                        let ta = crate::document_core::helpers::logical_to_text_offset(para, a).0;
                                        let tb = crate::document_core::helpers::logical_to_text_offset(para, b).0;
                                        let l = find_cursor_in_tree(tree, *pn, para_idx, ta, CursorBias::Leading);
                                        let r = find_cursor_in_tree(tree, *pn, para_idx, tb, CursorBias::Trailing);
                                        match (l, r) {
                                            (Some(l), Some(r)) if (r.x - l.x).abs() > 0.01 => {
                                                // 글자 조각의 높이는 표가 든 줄 전체 높이일 수 있다 — 세로는 캐럿(글자 크기)에서
                                                let caret = match cell_target {
                                                    None => self.get_cursor_rect_native(section_idx, para_idx, a),
                                                    Some(SelectionCellTarget::Flat {
                                                        parent_para_idx,
                                                        control_idx,
                                                        cell_idx,
                                                    }) => self.get_cursor_rect_in_cell_native(
                                                        section_idx,
                                                        parent_para_idx,
                                                        control_idx,
                                                        cell_idx,
                                                        para_idx,
                                                        a,
                                                    ),
                                                    Some(SelectionCellTarget::Path {
                                                        parent_para_idx,
                                                        path,
                                                    }) => {
                                                        let entries: Vec<String> = path
                                                            .iter()
                                                            .enumerate()
                                                            .map(|(i, e)| {
                                                                format!(
                                                                    "{{\"controlIndex\":{},\"cellIndex\":{},\"cellParaIndex\":{}}}",
                                                                    e.0,
                                                                    e.1,
                                                                    if i + 1 == path.len() { para_idx } else { e.2 }
                                                                )
                                                            })
                                                            .collect();
                                                        self.get_cursor_rect_by_path_native(
                                                            section_idx,
                                                            parent_para_idx,
                                                            &format!("[{}]", entries.join(",")),
                                                            a,
                                                        )
                                                    }
                                                };
                                                let (mut y, mut h) = (l.y, l.h);
                                                if let Ok(v) = caret
                                                    .ok()
                                                    .map(|s| serde_json::from_str::<serde_json::Value>(&s))
                                                    .transpose()
                                                    .map(|v| v.unwrap_or(serde_json::Value::Null))
                                                {
                                                    let cy = v.get("y").and_then(|x| x.as_f64());
                                                    let ch = v.get("height").and_then(|x| x.as_f64());
                                                    let cp = v.get("pageIndex").and_then(|x| x.as_u64());
                                                    if let (Some(cy), Some(ch), Some(cp)) = (cy, ch, cp) {
                                                        if cp as u32 == *pn && ch > 0.0 && l.h > ch * 2.5 && cy >= l.y - 1.0 && cy <= l.y + l.h {
                                                            y = (cy - ch * 0.2).max(l.y);
                                                            h = (ch * 1.4).min(l.y + l.h + ch * 0.2 - y);
                                                        }
                                                    }
                                                }
                                                Some((l.x.min(r.x), y, (r.x - l.x).abs(), h))
                                            }
                                            _ => None,
                                        }
                                    }
                                };
                                if let Some((bx, by, bw, bh)) = rect {
                                    rects.push(format!(
                                        "{{\"pageIndex\":{},\"x\":{:.1},\"y\":{:.1},\"width\":{:.1},\"height\":{:.1}}}",
                                        pn, bx, by, bw, bh
                                    ));
                                    last_segment_page = Some(*pn);
                                    hit_piece = true;
                                    break;
                                }
                            }
                        }
                        if hit_piece {
                            rendered_segments += 1;
                        }
                        continue;
                    }
                }

                let cursor_pair = tree_cache.iter().find_map(|(pn, tree)| {
