    /// [claude-hwpx cell-inline-caret] 표 칸 문단의 글자처럼 취급 그림 옆 캐럿. 칸 캐럿 함수는 글자 조각만 보아,
    /// 그림 둘만 있는 문단에서는 어느 위치든 첫 그림 가운데에 캐럿이 섰다(2026-09-27 실측, 위치 0~2 모두 x=267.2).
    /// 에디터는 개체를 포함한 위치(논리 위치)를 넘긴다. 그림 바로 앞이면 그림 왼쪽 끝, 바로 뒤면 오른쪽 끝을 돌려주고,
    /// 아니면 개체를 뺀 글자 위치로 바꿔 원래 처리에 넘긴다. 글자처럼 취급 그림이 없는 문단은 손대지 않는다.
    /// 반환: (캐럿 JSON, 원래 처리에 넘길 위치)
    pub(crate) fn claude_cell_inline_caret(
        &self,
        section_idx: usize,
        parent_para_idx: usize,
        control_idx: usize,
        cell_idx: usize,
        cell_para_idx: usize,
        offset: usize,
    ) -> Result<(Option<String>, usize), HwpError> {
        use crate::renderer::render_tree::{RenderNode, RenderNodeType};
        let para = match self
            .document
            .sections
            .get(section_idx)
            .and_then(|s| s.paragraphs.get(parent_para_idx))
            .and_then(|p| p.controls.get(control_idx))
        {
            Some(Control::Table(t)) => {
                match t.cells.get(cell_idx).and_then(|c| c.paragraphs.get(cell_para_idx)) {
                    Some(p) => p,
                    None => return Ok((None, offset)),
                }
            }
            _ => return Ok((None, offset)),
        };
        let tac_pics: Vec<usize> = para
            .controls
            .iter()
            .enumerate()
            .filter(|(_, c)| matches!(c, Control::Picture(p) if p.common.treat_as_char))
            .map(|(i, _)| i)
            .collect();
        if tac_pics.is_empty() {
            return Ok((None, offset));
        }
        let positions = find_logical_control_positions(para);
        let text_off = super::super::helpers::logical_to_text_offset(para, offset).0;
        let target = tac_pics
            .iter()
            .find(|&&k| positions.get(k).map_or(false, |&p| p + 1 == offset))
            .map(|&k| (k, true))
            .or_else(|| {
                tac_pics
                    .iter()
                    .find(|&&k| positions.get(k) == Some(&offset))
                    .map(|&k| (k, false))
            });
        let Some((k, after)) = target else {
            return Ok((None, text_off));
        };
        fn find_img(
            node: &RenderNode,
            sec: usize,
            ppi: usize,
            k: usize,
            b: &CellCursorBounds,
        ) -> Option<(f64, f64, f64, f64)> {
            if let RenderNodeType::Image(ref im) = node.node_type {
                if im.section_index == Some(sec)
                    && im.para_index == Some(ppi)
                    && im.control_index == Some(k)
                {
                    let cx = node.bbox.x + node.bbox.width / 2.0;
                    let cy = node.bbox.y + node.bbox.height / 2.0;
                    if cx >= b.x && cx <= b.x + b.w && cy >= b.y && cy <= b.y + b.h {
                        return Some((node.bbox.x, node.bbox.y, node.bbox.width, node.bbox.height));
                    }
                }
            }
            node.children.iter().find_map(|c| find_img(c, sec, ppi, k, b))
        }
        let pages = self.find_pages_for_cell_position(
            section_idx,
            parent_para_idx,
            control_idx,
            cell_idx,
            Some((cell_para_idx, text_off)),
        )?;
        for &page_num in &pages {
            let tree = self.build_page_tree(page_num)?;
            let Some(bounds) =
                find_table_cell_bounds_in_node(&tree.root, parent_para_idx, control_idx, cell_idx)
            else {
                continue;
            };
            if let Some((x, y, w, h)) = find_img(&tree.root, section_idx, parent_para_idx, k, &bounds) {
                let cx = if after { x + w } else { x };
                return Ok((Some(format_cursor_rect_json(page_num, cx, y, h, Some(bounds))), text_off));
            }
        }
        Ok((None, text_off))
    }

