        // [claude-hwpx cell-pic-delta] 바꾸기 전 그림 높이, 표 높이, 표를 담은 줄 높이, 그림 칸의 적힌 높이(아래 cell-pic-delta-after 가 쓴다)
        let claude_before: Option<(i32, i32, i32, u32)> = (path.len() == 1)
            .then(|| {
                let para = self
                    .document
                    .sections
                    .get(section_idx)?
                    .paragraphs
                    .get(parent_para_idx)?;
                let (tci, ci, cpi) = path[0];
                let Control::Table(t) = para.controls.get(tci)? else {
                    return None;
                };
                let cell = t.cells.get(ci)?;
                let pic_h = match cell.paragraphs.get(cpi)?.controls.get(inner_control_idx)? {
                    Control::Picture(p) => p.common.height as i32,
                    _ => return None,
                };
                Some((
                    pic_h,
                    t.common.height as i32,
                    para.line_segs.first()?.line_height,
                    cell.height,
                ))
            })
            .flatten();
