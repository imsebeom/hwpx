// ==== find ====
                        next_top = top.saturating_add(s.line_height).saturating_add(s.line_spacing.max(0));
                    }
                    end
                };
                let pad = if c.apply_inner_margin { &c.padding } else { &table.padding };
// ==== replace ====
                        next_top = top.saturating_add(s.line_height).saturating_add(s.line_spacing.max(0));
                    }
                    // [claude-hwpx ladder-pic-bottom] 칸 안 위아래 배치(문단 기준) 그림, 도형, 표는 저장 줄에 안 잡힌다 — 그 바닥도 사다리 끝으로 본다
                    // (결과보고서 216번 표 사진 칸: 줄 200, 그림 5308 → 한/글은 그림 높이로 행을 그린다)
                    for p in &c.paragraphs {
                        let para_top = p.line_segs.first().map(|s| s.vertical_pos).unwrap_or(0);
                        for ctl in &p.controls {
                            let common = match ctl {
                                Control::Picture(pic) => &pic.common,
                                Control::Shape(sh) => sh.common(),
                                // 위아래 배치 칸 안 표도 저장 줄에 안 잡힌다(정답본 d347 76번 표: 사다리 16778, 한/글 29822)
                                Control::Table(t) => &t.common,
                                _ => continue,
                            };
                            if common.treat_as_char
                                || !matches!(common.text_wrap, TextWrap::TopAndBottom)
                                || !matches!(common.vert_rel_to, VertRelTo::Para)
                            {
                                continue;
                            }
                            let bottom = para_top
                                .saturating_add((common.vertical_offset as i32).max(0))
                                .saturating_add(common.height.min(i32::MAX as u32) as i32)
                                .saturating_add(common.margin.top as i32)
                                .saturating_add(common.margin.bottom as i32);
                            end = end.max(bottom);
                        }
                    }
                    end
                };
                let pad = if c.apply_inner_margin { &c.padding } else { &table.padding };
