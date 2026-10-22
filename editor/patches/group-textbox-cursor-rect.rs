// ==== find ====
            if let Some((si, pi, ci)) = textbox_meta {
                textbox_bboxes.push(TextBoxBboxInfo {
// ==== replace ====
            // [claude-hwpx group-textbox] 글상자 노드를 실제로 가진 도형만 빈 자리 후보로 모은다. 묶음의 테두리 다각형(글상자 없음)이
            // 후보가 되어 그 자리를 누르면 없는 글상자로 들어가 글이 안 써졌다(워크시트 「단원 설계의 중점」 틀)
            let textbox_meta = textbox_meta
                .filter(|_| node.children.iter().any(|c| matches!(c.node_type, RenderNodeType::TextBox)));
            if let Some((si, pi, ci)) = textbox_meta {
                textbox_bboxes.push(TextBoxBboxInfo {
// ==== next ====
        struct TextBoxBboxInfo {
            section_index: usize,
            parent_para_index: usize,
            control_index: usize,
// ==== replace ====
        struct TextBoxBboxInfo {
            section_index: usize,
            parent_para_index: usize,
            control_index: usize,
            /// [claude-hwpx group-textbox] 묶음 자식 경로(묶음이 아니면 0)
            cell_index: usize,
// ==== next ====
                textbox_bboxes.push(TextBoxBboxInfo {
                    section_index: si,
                    parent_para_index: pi,
                    control_index: ci,
// ==== replace ====
                textbox_bboxes.push(TextBoxBboxInfo {
                    section_index: si,
                    parent_para_index: pi,
                    control_index: ci,
                    // [claude-hwpx group-textbox] 사각형은 그릴 때 실은 묶음 경로, 그 밖은 글자 조각의 경로에서
                    cell_index: match &node.node_type {
                        RenderNodeType::Rectangle(r) if r.claude_group_code != 0 => r.claude_group_code,
                        _ => claude_textbox_cell_index(node, ci),
                    },
// ==== next ====
        fn format_textbox_entry(tb: &TextBoxBboxInfo, page_num: u32) -> String {
// ==== replace ====
        /// [claude-hwpx group-textbox] 글상자 노드 아래 글자 조각의 셀 경로에서 이 글상자(개체 번호 ci)의 칸 번호(묶음 자식 경로)를 찾는다
        fn claude_textbox_cell_index(node: &RenderNode, ci: usize) -> usize {
            for ch in &node.children {
                if let RenderNodeType::TextRun(ref tr) = ch.node_type {
                    if let Some(ref ctx) = tr.cell_context {
                        if let Some(e) = ctx.path.iter().find(|e| e.control_index == ci) {
                            return e.cell_index;
                        }
                    }
                }
                let v = claude_textbox_cell_index(ch, ci);
                if v != 0 {
                    return v;
                }
            }
            0
        }

        fn format_textbox_entry(tb: &TextBoxBboxInfo, page_num: u32) -> String {
// ==== next ====
                if outer.cell_index == 0 {
                    let is_shape = self
                        .document
                        .sections
                        .get(run.section_index)
                        .and_then(|s| s.paragraphs.get(ctx.parent_para_index))
                        .and_then(|p| p.controls.get(outer.control_index))
                        .map(|c| matches!(c, Control::Shape(_)))
                        .unwrap_or(false);
                    run.is_textbox = is_shape;
                } else {
                    run.is_textbox = false;
                }
// ==== replace ====
                // [claude-hwpx group-textbox] 도형이면 칸 번호(묶음 자식 경로)와 상관없이 글상자다(표 칸은 개체가 표라 false)
                run.is_textbox = self
                    .document
                    .sections
                    .get(run.section_index)
                    .and_then(|s| s.paragraphs.get(ctx.parent_para_index))
                    .and_then(|p| p.controls.get(outer.control_index))
                    .map(|c| matches!(c, Control::Shape(_)))
                    .unwrap_or(false);
// ==== next ====
                 \"parentParaIndex\":{},\"controlIndex\":{},\"cellIndex\":0,\"cellParaIndex\":0,\
                 \"cellPath\":[{{\"controlIndex\":{},\"cellIndex\":0,\"cellParaIndex\":0}}],\
// ==== replace ====
                 \"parentParaIndex\":{},\"controlIndex\":{},\"cellIndex\":{},\"cellParaIndex\":0,\
                 \"cellPath\":[{{\"controlIndex\":{},\"cellIndex\":{},\"cellParaIndex\":0}}],\
// ==== next ====
                tb.section_index,
                tb.parent_para_index,
                tb.control_index,
                tb.control_index,
                page_num,
// ==== replace ====
                tb.section_index,
                tb.parent_para_index,
                tb.control_index,
                tb.cell_index,
                tb.control_index,
                tb.cell_index,
                page_num,
