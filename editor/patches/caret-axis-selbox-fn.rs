/// [claude-hwpx caret-axis] 렌더 트리에서 글자처럼 취급 표나 그림의 상자를 찾는다(선택 음영용).
/// 본문은 셀 문맥이 없는 노드, 셀은 글자 조각과 같은 셀 문맥 일치 규칙을 쓴다.
fn caret_axis_find_control_box(
    node: &crate::renderer::render_tree::RenderNode,
    sec: usize,
    para: usize,
    ci: usize,
    cell_target: Option<SelectionCellTarget<'_>>,
) -> Option<(f64, f64, f64, f64)> {
    let ids = match &node.node_type {
        crate::renderer::render_tree::RenderNodeType::Table(t) => Some((t.section_index, t.para_index, t.control_index, t.cell_context.as_ref())),
        crate::renderer::render_tree::RenderNodeType::Image(img) => Some((img.section_index, img.para_index, img.control_index, img.cell_context.as_ref())),
        // 수식은 셀 문맥 대신 cell_index 를 쓴다 — 본문 수식만 찾는다
        crate::renderer::render_tree::RenderNodeType::Equation(eq) if cell_target.is_none() && eq.cell_index.is_none() => {
            Some((eq.section_index, eq.para_index, eq.control_index, None))
        }
        _ => None,
    };
    if let Some((s, p, c, ctx)) = ids {
        let hit = match cell_target {
            None => s == Some(sec) && p == Some(para) && c == Some(ci) && ctx.is_none(),
            Some(target) => {
                c == Some(ci)
                    && ctx.is_some_and(|ctx| match target {
                        SelectionCellTarget::Flat {
                            parent_para_idx,
                            control_idx,
                            cell_idx,
                        } => flat_cell_ctx_matches(ctx, parent_para_idx, control_idx, cell_idx, para),
                        SelectionCellTarget::Path {
                            parent_para_idx,
                            path,
                        } => path_cell_ctx_matches(ctx, parent_para_idx, path, para),
                    })
            }
        };
        if hit && node.bbox.width > 0.0 && node.bbox.height > 0.0 {
            return Some((node.bbox.x, node.bbox.y, node.bbox.width, node.bbox.height));
        }
    }
    node.children
        .iter()
        .find_map(|child| caret_axis_find_control_box(child, sec, para, ci, cell_target))
}

