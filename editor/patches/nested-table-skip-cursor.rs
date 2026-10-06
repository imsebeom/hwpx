// ==== find ====
        let matches_table =
            table.para_index == Some(parent_para) && table.control_index == Some(ctrl_idx);
        if matches_table {
            for child in &node.children {
                if let RenderNodeType::TableCell(ref cell) = child.node_type {
                    if cell.model_cell_index == Some(c_idx as u32) {
// ==== replace ====
        // [claude-hwpx nested-table-skip-cursor] 번호로 찾는 칸 조회는 최외곽 표만(표 속 표는 칸 안 문단 번호라 겹칠 수 있다).
        // patches/nested-table-skip-bbox.rs 와 같은 까닭. 아래 세 곳도 같다
        let matches_table = table.para_index == Some(parent_para)
            && table.control_index == Some(ctrl_idx)
            && table.cell_context.is_none();
        if matches_table {
            for child in &node.children {
                if let RenderNodeType::TableCell(ref cell) = child.node_type {
                    if cell.model_cell_index == Some(c_idx as u32) {
// ==== next ====
                let matches_table =
                    tn.para_index == Some(parent_para) && tn.control_index == Some(ctrl_idx);
                if matches_table {
                    for child in &node.children {
                        if let RenderNodeType::TableCell(ref tc) = child.node_type {
                            if tc.col == target_col && tc.row == target_row {
// ==== replace ====
                let matches_table = tn.para_index == Some(parent_para)
                    && tn.control_index == Some(ctrl_idx)
                    && tn.cell_context.is_none();
                if matches_table {
                    for child in &node.children {
                        if let RenderNodeType::TableCell(ref tc) = child.node_type {
                            if tc.col == target_col && tc.row == target_row {
// ==== next ====
                RenderNodeType::Table(table_node) => {
                    if table_node.section_index == Some(sec) && table_node.para_index == Some(para)
                    {
                        if let Some(ci) = table_node.control_index {
// ==== replace ====
                RenderNodeType::Table(table_node) => {
                    if table_node.section_index == Some(sec)
                        && table_node.para_index == Some(para)
                        && table_node.cell_context.is_none()
                    {
                        if let Some(ci) = table_node.control_index {
// ==== next ====
                        RenderNodeType::Table(tn)
                            if tn.section_index == Some(sec) && tn.para_index == Some(para) =>
                        {
                            if is_caret_control(render_para, tn.control_index) {
// ==== replace ====
                        RenderNodeType::Table(tn)
                            if tn.section_index == Some(sec)
                                && tn.para_index == Some(para)
                                && tn.cell_context.is_none() =>
                        {
                            if is_caret_control(render_para, tn.control_index) {
