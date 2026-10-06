// ==== find ====
            if let RenderNodeType::Table(ref tn) = node.node_type {
                if tn.section_index == Some(sec)
                    && tn.para_index == Some(ppi)
                    && tn.control_index == Some(ci)
                {
                    return Some(format!(
// ==== replace ====
            if let RenderNodeType::Table(ref tn) = node.node_type {
                // [claude-hwpx nested-table-skip-bbox] 표 속 표는 칸 안에서의 문단 번호를 쓰므로 본문 표와 (문단, 컨트롤)
                // 번호가 겹칠 수 있다(문항카드: 3쪽 본문 표와 2쪽 그래프 상자가 둘 다 문단 7, 컨트롤 0). 번호로 찾는 조회는
                // 최외곽 표만 대상이다(cell_context 가 None) — 겹치면 다른 쪽에 선택 상자가 하나 더 그려지고 그 안의 그림이 눌리지 않았다
                if tn.section_index == Some(sec)
                    && tn.para_index == Some(ppi)
                    && tn.control_index == Some(ci)
                    && tn.cell_context.is_none()
                {
                    return Some(format!(
