// ==== find ====
            if let RenderNodeType::Table(ref tn) = node.node_type {
                if tn.section_index == Some(sec)
                    && tn.para_index == Some(ppi)
                    && tn.control_index == Some(ci)
                {
                    for (_child_idx, child) in node.children.iter().enumerate() {
// ==== replace ====
            if let RenderNodeType::Table(ref tn) = node.node_type {
                // [claude-hwpx nested-table-skip-cells] 번호로 찾는 칸 상자는 최외곽 표만(표 속 표는 경로 API). patches/nested-table-skip-bbox.rs 와 같은 까닭
                if tn.section_index == Some(sec)
                    && tn.para_index == Some(ppi)
                    && tn.control_index == Some(ci)
                    && tn.cell_context.is_none()
                {
                    for (_child_idx, child) in node.children.iter().enumerate() {
