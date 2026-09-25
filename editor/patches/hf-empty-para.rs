// ==== find ====
    for p in h.paragraphs.iter() {
        let (runs, linesegs, advance) = render_paragraph_parts(p, vert_cursor, ctx);
        vert_cursor = advance;
        let pid = ctx.next_para_id();
        let sid = ctx.effective_style_id(p.style_id);
        out.push_str(&render_hp_p_open(p, pid, sid));
        out.push_str(&runs);
        out.push_str(&linesegs);
        out.push_str("</hp:p>");
    }
    out.push_str(&format!("</hp:subList></hp:{tag}></hp:ctrl>", tag = tag));
// ==== replace ====
    for p in h.paragraphs.iter() {
        let (runs, linesegs, advance) = render_paragraph_parts(p, vert_cursor, ctx);
        vert_cursor = advance;
        let pid = ctx.next_para_id();
        let sid = ctx.effective_style_id(p.style_id);
        out.push_str(&render_hp_p_open(p, pid, sid));
        // [claude-hwpx hf-empty-para] 글이 없는 머리말 문단도 빈 run 하나를 둔다. `<hp:p></hp:p>` 는
        // rhwp 가 다시 읽을 때 버려, 그다음 저장에서 문단 없는 subList 가 되고 한/글이 그 파일을 열다 죽었다.
        if runs.is_empty() {
            out.push_str(r#"<hp:run charPrIDRef="0"/>"#);
        } else {
            out.push_str(&runs);
        }
        out.push_str(&linesegs);
        out.push_str("</hp:p>");
    }
    if h.paragraphs.is_empty() {
        let pid = ctx.next_para_id();
        out.push_str(&format!(
            r#"<hp:p id="{}" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="0"/></hp:p>"#,
            pid
        ));
    }
    out.push_str(&format!("</hp:subList></hp:{tag}></hp:ctrl>", tag = tag));
