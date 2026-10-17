// ==== find ====
    /// [claude-hwpx] 줄 배치 없이 글자처럼 취급하는 그림, 수식만 든 칸 문단. 다시 조판하지 않으면 줄 높이가 0 이라
// ==== replace ====
    /// [claude-hwpx cell-squeeze-one-line] 「한 줄로 입력」(lineWrap=SQUEEZE) 칸 문단은 한/글이 줄을 나누지 않고 자간을
    /// 줄여 한 줄에 넣는다(그리기 쪽 가로 축소는 rhwp 가 이미 한다). 줄 배치 없는 문서(스킬 산출물)는 문서를 열 때 칸 폭으로
    /// 줄을 나눠 「평가 / 영역」 두 줄이 되고 행이 한 줄만큼 커졌다(2026-10-17 교과 평가계획 5쪽 머리 행 26.6px, 한/글
    /// 18.2px). 넓은 상자로 다시 나눠 강제 줄바꿈만 남기고, 줄 기록의 상자(column_start, segment_width)는 칸 것으로 되돌린다
    fn claude_squeeze_one_line(
        para: &mut Paragraph,
        line_wrap: u8,
        inner_width_px: f64,
        styles: &ResolvedStyleSet,
        dpi: f64,
    ) {
        if line_wrap != crate::model::table::CELL_LINE_WRAP_SQUEEZE || para.line_segs.len() < 2 {
            return;
        }
        let (column_start, segment_width) =
            (para.line_segs[0].column_start, para.line_segs[0].segment_width);
        reflow_line_segs(
            para,
            ParagraphBox::content_width_px(inner_width_px.max(1.0) * 1000.0, dpi),
            styles,
            dpi,
        );
        for seg in &mut para.line_segs {
            seg.column_start = column_start;
            seg.segment_width = segment_width;
            // 계산한 줄(합성 표시)은 그릴 때 칸 폭으로 다시 나뉜다. 한/글이 저장했을 한 줄과 같으므로 저장 줄로 둔다
            seg.tag &= !LineSeg::TAG_IMPLEMENTATION_PROPERTY;
        }
    }

    /// [claude-hwpx] 줄 배치 없이 글자처럼 취급하는 그림, 수식만 든 칸 문단. 다시 조판하지 않으면 줄 높이가 0 이라
// ==== next ====
                            for cell_para in &mut cell.paragraphs {
                                // [#2195] 셀 NO_LS 확장은 **컨트롤 없는 순수 빈 문단**
// ==== replace ====
                            let cell_line_wrap = cell.line_wrap;
                            for cell_para in &mut cell.paragraphs {
                                // [#2195] 셀 NO_LS 확장은 **컨트롤 없는 순수 빈 문단**
// ==== next ====
                                    // 셀 내용 상자 — 열이 없으므로 원점은 셀 왼쪽
                                    // 끝이고 기하 피치를 적용하지 않는다. 스냅하면
                                    // 표 소유자가 이미 확정한 셀 폭을 흔든다.
                                    reflow_line_segs(
                                        cell_para,
                                        ParagraphBox::content_width_px(cell_inner_width, dpi),
                                        styles,
                                        dpi,
                                    );
// ==== replace ====
                                    // 셀 내용 상자 — 열이 없으므로 원점은 셀 왼쪽
                                    // 끝이고 기하 피치를 적용하지 않는다. 스냅하면
                                    // 표 소유자가 이미 확정한 셀 폭을 흔든다.
                                    reflow_line_segs(
                                        cell_para,
                                        ParagraphBox::content_width_px(cell_inner_width, dpi),
                                        styles,
                                        dpi,
                                    );
                                    Self::claude_squeeze_one_line(cell_para, cell_line_wrap, cell_inner_width, styles, dpi);
// ==== next ====
                            for cell_para in &mut cell.paragraphs {
                                if Self::needs_reflow_broadly(cell_para) {
                                    // 셀 내용 상자 — 위와 같은 이유로 미스냅.
                                    reflow_line_segs(
                                        cell_para,
                                        ParagraphBox::content_width_px(cell_inner_width, dpi),
                                        &styles,
                                        dpi,
                                    );
// ==== replace ====
                            let cell_line_wrap = cell.line_wrap;
                            for cell_para in &mut cell.paragraphs {
                                if Self::needs_reflow_broadly(cell_para) {
                                    // 셀 내용 상자 — 위와 같은 이유로 미스냅.
                                    reflow_line_segs(
                                        cell_para,
                                        ParagraphBox::content_width_px(cell_inner_width, dpi),
                                        &styles,
                                        dpi,
                                    );
                                    Self::claude_squeeze_one_line(cell_para, cell_line_wrap, cell_inner_width, &styles, dpi);
