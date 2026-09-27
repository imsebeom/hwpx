// ==== find ====
                            page_idx, rect_x, rect_y, width, rect_h
                        ));
                    }
                }
// ==== replace ====
                            page_idx, rect_x, rect_y, width, rect_h
                        ));
                    }
                } else {
                    // [claude-hwpx caret-axis] 글자 조각이 없는 줄(표나 그림만 있는 줄)은 캐럿을 못 찾는다.
                    // 그 줄 범위에 든 글자처럼 취급 개체의 상자로 음영을 채운다.
                    let slots = crate::document_core::helpers::caret_control_slots(para);
                    let mut hit_any = false;
                    for (ci, slot) in slots.iter().enumerate() {
                        let Some(slot) = slot else { continue };
                        if *slot < range_start || *slot >= range_end {
                            continue;
                        }
                        for (pn, tree) in &tree_cache {
                            if let Some((bx, by, bw, bh)) = caret_axis_find_control_box(
                                &tree.root,
                                section_idx,
                                para_idx,
                                ci,
                                cell_target,
                            ) {
                                rects.push(format!(
                                    "{{\"pageIndex\":{},\"x\":{:.1},\"y\":{:.1},\"width\":{:.1},\"height\":{:.1}}}",
                                    pn, bx, by, bw, bh
                                ));
                                last_segment_page = Some(*pn);
                                hit_any = true;
                                break;
                            }
                        }
                    }
                    if hit_any {
                        rendered_segments += 1;
                    }
                }
