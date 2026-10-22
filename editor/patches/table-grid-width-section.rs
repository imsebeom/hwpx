// ==== find ====
    materialize_hwpx_table_attrs(&mut table, table_record_flags);
    table.rebuild_grid();
    Ok(table)
}
// ==== replace ====
    materialize_hwpx_table_attrs(&mut table, table_record_flags);
    // [claude-hwpx table-grid-width] 칸 폭을 표 열 격자에 맞춘다(한/글 새 정답본 d007, d046, d200)
    claude_normalize_grid_widths(&mut table);
    table.rebuild_grid();
    Ok(table)
}

/// [claude-hwpx table-grid-width] 한/글은 칸마다 적힌 cellSz 가 아니라 표 열 격자로 칸 폭을 정한다. 열 폭은 그 열의 단일 열 칸 폭 최빈값(없으면
/// 병합 칸에서 뺌), 마지막 열은 표 폭 - 나머지 열 합(양수일 때), 칸 폭은 걸친 열 폭 합. 격자가 깨진 표, 칸 간격, 칸 안 표,
/// 열을 다 못 구한 표는 그대로 둔다.
fn claude_normalize_grid_widths(table: &mut Table) {
    let cols = table.col_count as usize;
    let rows = table.row_count as usize;
    if cols == 0 || rows == 0 || table.cell_spacing != 0 || table.cells.is_empty() {
        return;
    }
    let has_nested = table.cells.iter().any(|c| {
        c.paragraphs
            .iter()
            .any(|p| p.controls.iter().any(|ctl| matches!(ctl, crate::model::control::Control::Table(_))))
    });
    if has_nested {
        return;
    }
    let mut occ = vec![0u8; rows * cols];
    for c in &table.cells {
        let (r0, c0) = (c.row as usize, c.col as usize);
        let (rs, cs) = ((c.row_span as usize).max(1), (c.col_span as usize).max(1));
        if r0 + rs > rows || c0 + cs > cols {
            return;
        }
        for r in r0..r0 + rs {
            for k in c0..c0 + cs {
                occ[r * cols + k] = occ[r * cols + k].saturating_add(1);
            }
        }
    }
    if occ.iter().any(|&v| v != 1) {
        return;
    }
    let mut width: Vec<Option<i64>> = vec![None; cols];
    for k in 0..cols {
        let mut count: Vec<(u32, usize)> = Vec::new();
        for c in table.cells.iter().filter(|c| c.col as usize == k && c.col_span.max(1) == 1) {
            match count.iter_mut().find(|(w, _)| *w == c.width) {
                Some(e) => e.1 += 1,
                None => count.push((c.width, 1)),
            }
        }
        // 최빈값(같으면 먼저 나온 값)
        let mut best: Option<(u32, usize)> = None;
        for &(w, n) in &count {
            if best.map_or(true, |(_, bn)| n > bn) {
                best = Some((w, n));
            }
        }
        width[k] = best.map(|(w, _)| w as i64);
    }
    for _ in 0..cols {
        for c in &table.cells {
            let (c0, cs) = (c.col as usize, (c.col_span as usize).max(1));
            let unk: Vec<usize> = (c0..c0 + cs).filter(|&k| width[k].is_none()).collect();
            if unk.len() == 1 {
                let known: i64 = (c0..c0 + cs).filter_map(|k| width[k]).sum();
                width[unk[0]] = Some(c.width as i64 - known);
            }
        }
    }
    if width.iter().any(|w| w.map_or(true, |v| v <= 0)) {
        return;
    }
    let mut w: Vec<i64> = width.into_iter().map(|v| v.unwrap_or(0)).collect();
    let tw = table.common.width as i64;
    let others: i64 = w[..cols - 1].iter().sum();
    if tw > others {
        w[cols - 1] = tw - others;
    }
    for c in table.cells.iter_mut() {
        let (c0, cs) = (c.col as usize, (c.col_span as usize).max(1));
        let nw: i64 = w[c0..c0 + cs].iter().sum();
        if nw > 0 {
            c.width = nw as u32;
        }
    }
}
