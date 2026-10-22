// ==== find ====
                for (_ci, child) in group.children.iter().enumerate() {
                    let sa = child.shape_attr();
// ==== replace ====
                for (_ci, child) in group.children.iter().enumerate() {
                    // [claude-hwpx group-textbox] 묶음 자식의 글상자 글자는 칸 번호 자리에 자식 번호 경로를 싣는다(묶음 안 묶음 포함)
                    CLAUDE_GROUP_PATH.with(|p| {
                        let mut p = p.borrow_mut();
                        if _ci == 0 {
                            p.push(0);
                        }
                        if let Some(last) = p.last_mut() {
                            *last = _ci;
                        }
                    });
                    let sa = child.shape_attr();
// ==== next ====
                parent.children.push(group_node);
            }
            ShapeObject::Picture(pic) => {
// ==== replace ====
                // [claude-hwpx group-textbox] 묶음을 다 그렸으면 경로에서 이 묶음 자리를 뺀다
                if !group.children.is_empty() {
                    CLAUDE_GROUP_PATH.with(|p| {
                        p.borrow_mut().pop();
                    });
                }
                parent.children.push(group_node);
            }
            ShapeObject::Picture(pic) => {
// ==== next ====
fn textbox_vpos_origin_hu(common: &CommonObjAttr, matrix_positioned: bool) -> Option<i32> {
// ==== replace ====
thread_local! {
    /// [claude-hwpx group-textbox] 지금 그리는 묶음 자식 번호 경로(바깥 묶음부터, 글상자 경로 칸 번호로 싣는다)
    pub(crate) static CLAUDE_GROUP_PATH: std::cell::RefCell<Vec<usize>> = const { std::cell::RefCell::new(Vec::new()) };
}

/// [claude-hwpx group-textbox] 글상자 셀 경로의 칸 번호: 묶음 자식이면 자식 번호 경로, 아니면 0
fn claude_group_cell_index() -> usize {
    CLAUDE_GROUP_PATH.with(|g| {
        let g = g.borrow();
        if g.is_empty() { 0 } else { crate::document_core::helpers::claude_group_path_encode(&g) }
    })
}

fn textbox_vpos_origin_hu(common: &CommonObjAttr, matrix_positioned: bool) -> Option<i32> {
// ==== next ====
                                control_index,
                                cell_index: 0,
                                cell_para_index: tb_para_idx,
// ==== replace ====
                                control_index,
                                cell_index: claude_group_cell_index(), // [claude-hwpx group-textbox]
                                cell_para_index: tb_para_idx,
// ==== next ====
                        control_index,
                        cell_index: 0,
                        cell_para_index: tb_para_idx,
// ==== replace ====
                        control_index,
                        cell_index: claude_group_cell_index(), // [claude-hwpx group-textbox]
                        cell_para_index: tb_para_idx,
// ==== next ====
                            control_index,
                            cell_index: 0,
                            cell_para_index: ci.cell_para_index,
// ==== replace ====
                            control_index,
                            cell_index: claude_group_cell_index(), // [claude-hwpx group-textbox]
                            cell_para_index: ci.cell_para_index,
// ==== next ====
                        let pic_cell_ctx = CellContext {
                            in_textbox: true,
                            parent_para_index: para_index,
                            path: {
                                let mut p = parent_cell_path.to_vec();
                                p.push(CellPathEntry {
                                    control_index,
                                    cell_index: 0,
// ==== replace ====
                        let pic_cell_ctx = CellContext {
                            in_textbox: true,
                            parent_para_index: para_index,
                            path: {
                                let mut p = parent_cell_path.to_vec();
                                p.push(CellPathEntry {
                                    control_index,
                                    cell_index: claude_group_cell_index(), // [claude-hwpx group-textbox]
// ==== next ====
                        let equiv_cell_ctx = CellContext {
                            in_textbox: true,
                            parent_para_index: para_index,
                            path: {
                                let mut p = parent_cell_path.to_vec();
                                p.push(CellPathEntry {
                                    control_index,
                                    cell_index: 0,
// ==== replace ====
                        let equiv_cell_ctx = CellContext {
                            in_textbox: true,
                            parent_para_index: para_index,
                            path: {
                                let mut p = parent_cell_path.to_vec();
                                p.push(CellPathEntry {
                                    control_index,
                                    cell_index: claude_group_cell_index(), // [claude-hwpx group-textbox]
