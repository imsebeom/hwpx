// ==== find ====
            if let Some(memo_children) = super::field::memo_field_children_xml(f) {
                out.push_str(&super::field::field_begin_open_tag(f));
                out.push('>');
                out.push_str(&memo_children);
// ==== replace ====
            if let Some(memo_children) = super::field::memo_field_children_xml(f) {
                out.push_str(&super::field::field_begin_open_tag(f));
                out.push('>');
                // [claude-hwpx memo-list-hwp5] 이 갈래는 빈 본문을 고정으로 쓴다. HWP5 메모 목록에서 읽은 본문이 있으면 그 문단을 쓴다
                if f.memo_paragraphs.is_empty() {
                    out.push_str(&memo_children);
                } else {
                    let params_end = memo_children.find("<hp:subList").unwrap_or(memo_children.len());
                    out.push_str(&memo_children[..params_end]);
                    out.push_str(&render_sub_list_open(f.memo_text_direction.as_deref()));
                    let mut vert_cursor: u32 = 0;
                    for para in &f.memo_paragraphs {
                        ctx.para_shape_ids.reference(para.para_shape_id);
                        let sid = ctx.effective_style_id(para.style_id);
                        ctx.style_ids.reference(sid as u16);
                        let (runs, linesegs, advance) = render_paragraph_parts(para, vert_cursor, ctx);
                        vert_cursor = advance;
                        let pid = ctx.next_para_id();
                        out.push_str(&render_hp_p_open(para, pid, sid));
                        out.push_str(&runs);
                        out.push_str(&linesegs);
                        out.push_str("</hp:p>");
                    }
                    out.push_str("</hp:subList>");
                }
