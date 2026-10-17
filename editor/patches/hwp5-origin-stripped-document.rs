// ==== find ====
        let hwp5_origin_hwpx = matches!(source_format, crate::parser::FileFormat::Hwpx)
            && document
                .hwpx_aux_entry(crate::model::document::HWP5_ORIGIN_HWPX_MARKER_PATH)
                .is_some();
// ==== replace ====
        let hwp5_origin_hwpx = matches!(source_format, crate::parser::FileFormat::Hwpx)
            && document
                .hwpx_aux_entry(crate::model::document::HWP5_ORIGIN_HWPX_MARKER_PATH)
                .is_some()
            // [claude-hwpx hwp5-origin-stripped] 본문 문단 전체에 줄 배치가 하나도 없으면 HWP5 의 빈 줄이 아니라 지운 캐시다(스킬 저장본) — XML 처럼 다시 만든다
            && document
                .sections
                .iter()
                .flat_map(|section| section.paragraphs.iter())
                .any(|para| !para.line_segs.is_empty());
