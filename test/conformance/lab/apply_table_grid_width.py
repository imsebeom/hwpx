"""개발용: HWPX 표를 읽을 때 칸 폭을 표 열 격자에 맞춘다(한/글처럼).

    python apply_table_grid_width.py [--revert]

근거(새 정답본): 한/글은 칸마다 적힌 cellSz 가 아니라 표 전체의 열 격자로 칸 폭을 정한다.
- d200: 0행 (2열, 2열 병합) 칸이 2764 로 적혀 있지만 줄 폭 4508 = 2열 2764 + 3열 2765 - 여백 1020.
- d007: 1열이 행마다 27600, 30523, 35907 로 다르게 적혀 있지만 모든 행을 표 폭 47907 - 0열 12000 로 조판.
- d046: 표 폭 45483 > 칸 합 45183 이면 마지막 열이 그 차이(300)만큼 넓다.
열 폭 = 그 열에서 시작하는 단일 열 칸 폭의 최빈값(없으면 병합 칸에서 뺌, 걸친 열 가운데 하나만 모를 때), 마지막 열 = 표 폭 - 나머지 열 합
(양수일 때), 칸 폭 = 걸친 열 폭 합. 칸이 격자를 정확히 한 번씩 덮지 않는 표(d223 의 겹친 칸), 칸 간격이 있는 표, 칸 안에 표가 든 표,
열을 다 못 구한 표는 그대로 둔다. 정답본 사본을 이 규칙으로 고쳐 채점하면 불일치 181 → 174, 새로 틀린 줄 0(scratchpad grid_fix.py).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx table-grid-width]"

EDITS = [
    (
        "parser/hwpx/section.rs",
        "    materialize_hwpx_table_attrs(&mut table, table_record_flags);\n    table.rebuild_grid();\n    Ok(table)\n}\n",
        "    materialize_hwpx_table_attrs(&mut table, table_record_flags);\n"
        f"    // {TAG} 칸 폭을 표 열 격자에 맞춘다(한/글 새 정답본 d007, d046, d200)\n"
        "    claude_normalize_grid_widths(&mut table);\n"
        "    table.rebuild_grid();\n"
        "    Ok(table)\n"
        "}\n"
        "\n"
        f"/// {TAG} 한/글은 칸마다 적힌 cellSz 가 아니라 표 열 격자로 칸 폭을 정한다. 열 폭은 그 열의 단일 열 칸 폭 최빈값(없으면\n"
        "/// 병합 칸에서 뺌), 마지막 열은 표 폭 - 나머지 열 합(양수일 때), 칸 폭은 걸친 열 폭 합. 격자가 깨진 표, 칸 간격, 칸 안 표,\n"
        "/// 열을 다 못 구한 표는 그대로 둔다.\n"
        "fn claude_normalize_grid_widths(table: &mut Table) {\n"
        "    let cols = table.col_count as usize;\n"
        "    let rows = table.row_count as usize;\n"
        "    if cols == 0 || rows == 0 || table.cell_spacing != 0 || table.cells.is_empty() {\n"
        "        return;\n"
        "    }\n"
        "    let has_nested = table.cells.iter().any(|c| {\n"
        "        c.paragraphs\n"
        "            .iter()\n"
        "            .any(|p| p.controls.iter().any(|ctl| matches!(ctl, crate::model::control::Control::Table(_))))\n"
        "    });\n"
        "    if has_nested {\n"
        "        return;\n"
        "    }\n"
        "    let mut occ = vec![0u8; rows * cols];\n"
        "    for c in &table.cells {\n"
        "        let (r0, c0) = (c.row as usize, c.col as usize);\n"
        "        let (rs, cs) = ((c.row_span as usize).max(1), (c.col_span as usize).max(1));\n"
        "        if r0 + rs > rows || c0 + cs > cols {\n"
        "            return;\n"
        "        }\n"
        "        for r in r0..r0 + rs {\n"
        "            for k in c0..c0 + cs {\n"
        "                occ[r * cols + k] = occ[r * cols + k].saturating_add(1);\n"
        "            }\n"
        "        }\n"
        "    }\n"
        "    if occ.iter().any(|&v| v != 1) {\n"
        "        return;\n"
        "    }\n"
        "    let mut width: Vec<Option<i64>> = vec![None; cols];\n"
        "    for k in 0..cols {\n"
        "        let mut count: Vec<(u32, usize)> = Vec::new();\n"
        "        for c in table.cells.iter().filter(|c| c.col as usize == k && c.col_span.max(1) == 1) {\n"
        "            match count.iter_mut().find(|(w, _)| *w == c.width) {\n"
        "                Some(e) => e.1 += 1,\n"
        "                None => count.push((c.width, 1)),\n"
        "            }\n"
        "        }\n"
        "        // 최빈값(같으면 먼저 나온 값)\n"
        "        let mut best: Option<(u32, usize)> = None;\n"
        "        for &(w, n) in &count {\n"
        "            if best.map_or(true, |(_, bn)| n > bn) {\n"
        "                best = Some((w, n));\n"
        "            }\n"
        "        }\n"
        "        width[k] = best.map(|(w, _)| w as i64);\n"
        "    }\n"
        "    for _ in 0..cols {\n"
        "        for c in &table.cells {\n"
        "            let (c0, cs) = (c.col as usize, (c.col_span as usize).max(1));\n"
        "            let unk: Vec<usize> = (c0..c0 + cs).filter(|&k| width[k].is_none()).collect();\n"
        "            if unk.len() == 1 {\n"
        "                let known: i64 = (c0..c0 + cs).filter_map(|k| width[k]).sum();\n"
        "                width[unk[0]] = Some(c.width as i64 - known);\n"
        "            }\n"
        "        }\n"
        "    }\n"
        "    if width.iter().any(|w| w.map_or(true, |v| v <= 0)) {\n"
        "        return;\n"
        "    }\n"
        "    let mut w: Vec<i64> = width.into_iter().map(|v| v.unwrap_or(0)).collect();\n"
        "    let tw = table.common.width as i64;\n"
        "    let others: i64 = w[..cols - 1].iter().sum();\n"
        "    if tw > others {\n"
        "        w[cols - 1] = tw - others;\n"
        "    }\n"
        "    for c in table.cells.iter_mut() {\n"
        "        let (c0, cs) = (c.col as usize, (c.col_span as usize).max(1));\n"
        "        let nw: i64 = w[c0..c0 + cs].iter().sum();\n"
        "        if nw > 0 {\n"
        "            c.width = nw as u32;\n"
        "        }\n"
        "    }\n"
        "}\n",
    ),
]


def main():
    revert = "--revert" in sys.argv
    for rel, find, repl in EDITS:
        if revert:
            find, repl = repl, find
        f = SRC / rel
        raw = f.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        s = raw.replace("\r\n", "\n")
        if (find not in s) if revert else (repl in s):
            print("이미", rel)
            continue
        n = s.count(find)
        if n != 1:
            sys.exit(f"{rel}: 자리 {n}곳 — {find[:50]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel)


if __name__ == "__main__":
    main()
