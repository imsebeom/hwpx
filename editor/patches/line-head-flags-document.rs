// ==== find ====
        let styles = resolve_styles_for_document(&document, DEFAULT_DPI);

        let hwp5_origin_hwpx = matches!(source_format, crate::parser::FileFormat::Hwpx)
// ==== replace ====
        let styles = resolve_styles_for_document(&document, DEFAULT_DPI);
        // [claude-hwpx line-head-flags]
        if matches!(source_format, crate::parser::FileFormat::Hwpx) {
            for sec in document.sections.iter_mut() {
                crate::renderer::composer::claude_repair_line_head_flags(&mut sec.paragraphs, &styles);
            }
        }

        let hwp5_origin_hwpx = matches!(source_format, crate::parser::FileFormat::Hwpx)
