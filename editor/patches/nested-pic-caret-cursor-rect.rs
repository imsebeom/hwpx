// ==== find ====
    /// 페이지 좌표에서 문서 위치 찾기 (네이티브)
// ==== replace ====
    /// [claude-hwpx nested-pic-caret] 표 속 표 칸 문단의 글자처럼 취급 그림 옆 캐럿 (쪽, x, y, 높이). 그림 앞이면 왼쪽 끝, 뒤면 오른쪽 끝.
    pub(crate) fn claude_nested_pic_caret(
        &self,
        section_idx: usize,
        parent_para_idx: usize,
        path: &[(usize, usize, usize)],
        offset: usize,
    ) -> Option<(u32, f64, f64, f64)> {
        use crate::renderer::render_tree::{RenderNode, RenderNodeType};
        let para = self.resolve_paragraph_by_path(section_idx, parent_para_idx, path).ok()?;
        let positions = find_logical_control_positions(para);
        let tac: Vec<usize> = para
            .controls
            .iter()
            .enumerate()
            .filter(|(_, c)| matches!(c, Control::Picture(p) if p.common.treat_as_char))
            .map(|(i, _)| i)
            .collect();
        let (k, after) = tac
            .iter()
            .find(|&&k| positions.get(k).map_or(false, |&p| p + 1 == offset))
            .map(|&k| (k, true))
            .or_else(|| tac.iter().find(|&&k| positions.get(k) == Some(&offset)).map(|&k| (k, false)))?;
        let Control::Picture(pic) = para.controls.get(k)? else {
            return None;
        };
        let bin = pic.image_attr.bin_data_id;
        fn find_img(node: &RenderNode, sec: usize, bin: u16) -> Option<(f64, f64, f64, f64)> {
            if let RenderNodeType::Image(ref im) = node.node_type {
                if im.section_index == Some(sec) && im.bin_data_id == bin {
                    return Some((node.bbox.x, node.bbox.y, node.bbox.width, node.bbox.height));
                }
            }
            node.children.iter().find_map(|c| find_img(c, sec, bin))
        }
        let (c0, c1, c2) = *path.first()?;
        let pages = self
            .find_pages_for_cell_position(section_idx, parent_para_idx, c0, c1, Some((c2, 0)))
            .ok()?;
        for &page_num in &pages {
            let Ok(tree) = self.build_page_tree(page_num) else {
                continue;
            };
            if let Some((x, y, w, h)) = find_img(&tree.root, section_idx, bin) {
                return Some((page_num, if after { x + w } else { x }, y, h));
            }
        }
        None
    }

    /// [claude-hwpx nested-pic-caret] 글 없이 그림만 있는 표 속 표 칸 문단을 눌렀을 때 클릭 x 에 가장 가까운 자리와 캐럿 x.
    pub(crate) fn claude_nested_pic_hit(
        &self,
        section_idx: usize,
        parent_para_idx: usize,
        path: &[(usize, usize, usize)],
        x: f64,
    ) -> Option<(usize, f64)> {
        let para = self.resolve_paragraph_by_path(section_idx, parent_para_idx, path).ok()?;
        if !para.text.trim().is_empty()
            || !para.controls.iter().any(|c| matches!(c, Control::Picture(p) if p.common.treat_as_char))
        {
            return None;
        }
        let slots = para.controls.iter().filter(|c| c.is_logical_inline()).count();
        let mut best: Option<(usize, f64)> = None;
        for off in 0..=slots {
            let Some((_, cx, _, _)) = self.claude_nested_pic_caret(section_idx, parent_para_idx, path, off) else {
                continue;
            };
            if best.map_or(true, |(_, bx)| (cx - x).abs() < (bx - x).abs()) {
                best = Some((off, cx));
            }
        }
        best
    }

    /// 페이지 좌표에서 문서 위치 찾기 (네이티브)
// ==== next ====
if let Some(ctx) = runs[idx].cell_context.as_ref().filter(|c| c.path.len() == 1) {
// ==== replace ====
if let Some(ctx) = runs[idx].cell_context.as_ref().filter(|c| c.path.len() > 1) {
                        let p: Vec<(usize, usize, usize)> =
                            ctx.path.iter().map(|e| (e.control_index, e.cell_index, e.cell_para_index)).collect();
                        if let Some((off, cx)) = self.claude_nested_pic_hit(runs[idx].section_index, ctx.parent_para_index, &p, x) {
                            return Ok(Self::claude_hit_with_x(format_hit(&runs[idx], off, page_num), cx));
                        }
                    }
                    if let Some(ctx) = runs[idx].cell_context.as_ref().filter(|c| c.path.len() == 1) {
// ==== next ====
if let Some(ctx) = line_runs[idx].cell_context.as_ref().filter(|c| c.path.len() == 1) {
// ==== replace ====
if let Some(ctx) = line_runs[idx].cell_context.as_ref().filter(|c| c.path.len() > 1) {
                        let p: Vec<(usize, usize, usize)> =
                            ctx.path.iter().map(|e| (e.control_index, e.cell_index, e.cell_para_index)).collect();
                        if let Some((off, cx)) = self.claude_nested_pic_hit(line_runs[idx].section_index, ctx.parent_para_index, &p, x) {
                            return Ok(Self::claude_hit_with_x(format_hit(line_runs[idx], off, page_num), cx));
                        }
                    }
                    if let Some(ctx) = line_runs[idx].cell_context.as_ref().filter(|c| c.path.len() == 1) {
// ==== next ====
        } else {
            char_offset
        };
// ==== replace ====
        } else {
            if let Some((pg, x, y, h)) =
                self.claude_nested_pic_caret(section_idx, parent_para_idx, &path, char_offset)
            {
                return Ok(format_cursor_rect_json(pg, x, y, h, None));
            }
            char_offset
        };
