// ==== find ====
                if content > decl_h
                    && cell
                        .paragraphs
                        .iter()
                        .all(crate::renderer::para_has_no_stored_line_segs)
// ==== replace ====
                if content > decl_h
                    // [claude-hwpx cut-row-pad-stored] HWPX 는 저장 줄 기록이 있어도 같다(issue1949 머리 행: 한/글 PDF 행 간격 1486 HU = 1200 + 141 + 141)
                    && (self.profile.get().hwpx_container()
                        || cell
                            .paragraphs
                            .iter()
                            .all(crate::renderer::para_has_no_stored_line_segs))
