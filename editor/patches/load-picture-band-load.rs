// ==== find ====
                                );
                            }
                        }
                    }
                }
            }

            // HWPX: LINE_SEG를 실제로 합성/보정한 경우에만 문단 간 vpos를 재계산한다.
// ==== replace ====
                                );
                            }
                        }
                    }
                }
            }

            // [claude-hwpx load-picture-band] 줄 배치를 합성한 문단이 어울림(Square) 그림 옆에 있으면 그 띠로 다시 짠다.
            // 한/글은 그림을 품은 문단과 뒤 문단들을 그림 옆 띠에서 시작한다(한국문화 14단원 마지막 쪽: 한/글 재저장
            // horzpos 34627, 폭 13561 — 그림 문단, 빈 문단, 표 문단 모두). 합성 줄은 단 전체 폭이라 그림 위에 겹쳤다.
            // 편집 경로가 쓰는 같은 띠 계산(layout_picture_band)을 쓰고, 저장 줄 배치가 있는 문단은 건드리지 않는다
            if body_line_seg_changed {
                let mut hi = 0usize;
                while hi < section.paragraphs.len() {
                    let is_host = section.paragraphs[hi].controls.iter().any(|c| {
                        matches!(c, Control::Picture(p)
                            if !p.common.treat_as_char
                                && p.common.text_wrap == crate::model::shape::TextWrap::Square)
                    });
                    if !is_host {
                        hi += 1;
                        continue;
                    }
                    let band = crate::renderer::composer::claude_layout_picture_band_to_doc_end(
                        &section.paragraphs,
                        hi,
                        col_width,
                        styles,
                        dpi,
                    );
                    let Some(band) = band else {
                        hi += 1;
                        continue;
                    };
                    // 띠 안에서 처음 합성한 문단부터 뒤는 모두 띠 줄로 바꾼다 — 앞 흐름이 바뀌었으면 뒤 문단의 저장 줄도
                    // 그 전 흐름으로 잰 낡은 값이다(14단원 표 문단은 삽화를 넣기 전의 horzpos 0 을 그대로 갖고 있었다)
                    let range = band.paragraph_range.clone();
                    let first_synth = range.clone().find(|pi| reflowed_paras.contains(pi));
                    for (pi, segs) in range.clone().zip(band.line_segs) {
                        if first_synth.is_some_and(|first| pi >= first) {
                            section.paragraphs[pi].replace_line_segs(segs);
                            reflowed_paras.insert(pi);
                        }
                    }
                    hi = range.end.max(hi + 1);
                }
            }

            // HWPX: LINE_SEG를 실제로 합성/보정한 경우에만 문단 간 vpos를 재계산한다.
