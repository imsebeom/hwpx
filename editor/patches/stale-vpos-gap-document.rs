// ==== find ====
            for sec in document.sections.iter_mut() {
                crate::renderer::composer::claude_repair_line_head_flags(&mut sec.paragraphs, &styles);
            }
// ==== replace ====
            let para_shapes = document.doc_info.para_shapes.clone();
            for sec in document.sections.iter_mut() {
                crate::renderer::composer::claude_repair_line_head_flags(&mut sec.paragraphs, &styles);
                // [claude-hwpx stale-vpos-gap]
                crate::renderer::composer::claude_close_stale_vpos_gaps(&mut sec.paragraphs, &para_shapes);
            }
