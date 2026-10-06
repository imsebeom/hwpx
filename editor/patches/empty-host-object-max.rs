// ==== find ====
    pub row_block_end: Vec<usize>,
}
// ==== replace ====
    pub row_block_end: Vec<usize>,
}

/// [claude-hwpx empty-host-object-max] 글 없는 문단에 든 위아래 배치(글자처럼 취급 아님) 개체는 그 빈 줄과 겹친다.
///
/// 한/글은 다음 문단을 max(빈 줄 진행, 개체 흐름 높이)에 둔다 — CORE 실적표 한/글 재저장: 그림 1559 → 다음 문단 1600,
/// 그림 1617 → 1617, 그림 1824 → 1824(빈 줄은 모두 1000 + 600). 줄 합과 개체 높이를 따로 더하는 셈에서 뺄 겹침
/// (= min(빈 줄 진행, 개체 높이))을 돌려준다. 글이 있는 문단은 0.
pub(crate) fn claude_empty_host_flow_overlap_px(
    para: &Paragraph,
    object_flow_px: f64,
    dpi: f64,
) -> f64 {
    if object_flow_px <= 0.0
        || para
            .text
            .chars()
            .any(|ch| ch > '\u{001F}' && ch != '\u{FFFC}' && !ch.is_whitespace())
    {
        return 0.0;
    }
    let advance = para
        .line_segs
        .first()
        .map(|s| hwpunit_to_px(s.line_height.saturating_add(s.line_spacing.max(0)), dpi))
        .unwrap_or(0.0);
    advance.min(object_flow_px).max(0.0)
}
// ==== next ====

    /// [#6124] 비례 축소로 내용 아래까지 눌린 세로 병합 묶음을 되돌린다.
// ==== replace ====

    /// [claude-hwpx empty-host-object-max] 줄 합 + `measure_non_inline_controls_height` 로 더하는 셈에서 뺄 빈 앵커 문단 겹침.
    fn claude_empty_host_overlap(&self, paragraphs: &[Paragraph]) -> f64 {
        paragraphs
            .iter()
            .map(|para| {
                let flow = para
                    .controls
                    .iter()
                    .map(|ctrl| match ctrl {
                        Control::Picture(pic) => self.non_inline_control_flow_height(&pic.common),
                        Control::Shape(shape) => self.non_inline_control_flow_height(shape.common()),
                        _ => 0.0,
                    })
                    .fold(0.0f64, f64::max);
                claude_empty_host_flow_overlap_px(para, flow, self.dpi)
            })
            .sum()
    }

    /// [#6124] 비례 축소로 내용 아래까지 눌린 세로 병합 묶음을 되돌린다.
// ==== next ====
                    };
                    let additive = text_height + non_inline_h;
                    // trust 는 "저장 ladder 가 개체 밀림을 이미 반영한" 셀에만 —
// ==== replace ====
                    };
                    // [claude-hwpx empty-host-object-max] 빈 앵커 문단의 줄과 개체는 겹친다(max, 합 아님)
                    let additive =
                        text_height + non_inline_h - self.claude_empty_host_overlap(&cell.paragraphs);
                    // trust 는 "저장 ladder 가 개체 밀림을 이미 반영한" 셀에만 —
// ==== next ====
                } else {
                    let content_height = (text_height + non_inline_h)
                        .max(nested_bottom)
// ==== replace ====
                } else {
                    // [claude-hwpx empty-host-object-max]
                    let content_height = (text_height + non_inline_h
                        - self.claude_empty_host_overlap(&cell.paragraphs))
                        .max(nested_bottom)
