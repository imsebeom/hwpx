// ==== find ====
                .into_iter()
                .collect(),
            ..Paragraph::new_empty()
        }
    }
// ==== replace ====
                .into_iter()
                .collect(),
            // [claude-hwpx empty-like-seg] 줄 배치도 split_at 처럼 앞 문단 첫 줄의 치수와 표식을 물려받는다(세로 위치는 0 —
            // 호출측 recalc 가 흐름에 잇는다). 종전에는 기본 줄 배치(합성 표식 없음)라, 줄 배치가 없는 문서(합성 줄만 있음)에
            // insertParagraph 로 넣은 문단만 저장 줄 배치처럼 다뤄져 그 세로 위치가 뒤 문단의 기준점이 됐다. Enter(split_at)로 넣은
            // 같은 글은 처음부터 조판한 것과 쪽이 같은데 이 경로만 뒤 문단이 한 쪽 밀렸다(2026-10-25 편집 순서 시험 insert_paragraphs)
            line_segs: match template.line_segs.first() {
                Some(o) if o.line_height > 0 => vec![LineSeg {
                    text_start: 0,
                    line_height: o.line_height,
                    text_height: o.text_height,
                    baseline_distance: o.baseline_distance,
                    line_spacing: o.line_spacing,
                    segment_width: o.segment_width,
                    tag: o.tag,
                    ..Default::default()
                }],
                _ => Paragraph::new_empty().line_segs,
            },
            ..Paragraph::new_empty()
        }
    }
