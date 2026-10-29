"""개발용: HWPX 글자처럼 취급 표에 한 행 칸이 없는 행이 있으면 행 높이를 위에서부터 차례로 다시 정한다.

    python apply_span_topdown.py [--revert]

근거(결과보고서 29, 30쪽 163, 164번 표, 7~11행): 10행은 병합 칸에만 걸친 행이다. 2-b 풀이가 짧은 병합부터 풀어 0열 10~11행 칸 선언
(4570, 내용은 5348)에서 11행 내용(31.3px)을 빼 10행을 29.5px 로 먼저 정했고, 2-c 가 0열 칸의 부족분을 11행에 더해 11행이 41.7px 였다.
한/글은 8~10행 칸 그림 중심(한/글 409.5, 엔진 413.2)과 11행 가운데 정렬 글로 보아 10행 = 8~10행 칸 선언 - 8행 - 9행(약 21.7px),
11행 = 0열 칸 내용 - 10행(약 49.6px)이다. 위에서부터 행마다 「한 행 칸 높이」와 「그 행에서 끝나는 병합 칸의 모자란 몫」 중 큰 값을 쓰면
이 값이 나온다. 병합 칸 몫은 내용과 선언 중 큰 값(미뤄 둔 선언 보충 #2291 과 같은 규칙)이다. 한 행 칸 없는 행이 없는 표는 그대로 둔다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx span-topdown]"

EDITS = [
    (
        "renderer/height_measurer.rs",
        "        // 2-b단계: 병합 셀에서 미지 행 높이를 반복적으로 해결\n",
        (
            f"        // {TAG} 한 행 칸으로 정한 행 높이(위에서부터 다시 풀 때 바닥)\n"
            "        let claude_h1 = row_heights.clone();\n"
            "        // 2-b단계: 병합 셀에서 미지 행 높이를 반복적으로 해결\n"
        ),
    ),
    (
        "renderer/height_measurer.rs",
        (
            "        // 2-c단계: 병합 셀의 실제 컨텐츠 높이가 결합 행 높이 초과 시 마지막 행 확장\n"
            "        for cell in &table.cells {\n"
        ),
        (
            "        // 2-c단계: 병합 셀의 실제 컨텐츠 높이가 결합 행 높이 초과 시 마지막 행 확장\n"
            f"        // {TAG} 병합 칸마다 (시작 행, 걸친 행 수, 내용과 선언 중 큰 값)\n"
            "        let mut claude_span_req: Vec<(usize, usize, f64)> = Vec::new();\n"
            "        for cell in &table.cells {\n"
        ),
    ),
    (
        "renderer/height_measurer.rs",
        (
            "                let combined: f64 = (r..r + span).map(|i| row_heights[i]).sum();\n"
            "                if required_height > combined {\n"
            "                    let deficit = required_height - combined;\n"
            "                    row_heights[r + span - 1] += deficit;\n"
            "                }\n"
            "            }\n"
            "        }\n"
            "\n"
            "        // [claude-hwpx span-ladder-trust] 미뤄 둔"
        ),
        (
            f"                // {TAG}\n"
            "                let claude_decl = if cell.height < 0x8000_0000 { hwpunit_to_px(cell.height as i32, self.dpi) } else { 0.0 };\n"
            "                claude_span_req.push((r, span, required_height.max(claude_decl)));\n"
            "                let combined: f64 = (r..r + span).map(|i| row_heights[i]).sum();\n"
            "                if required_height > combined {\n"
            "                    let deficit = required_height - combined;\n"
            "                    row_heights[r + span - 1] += deficit;\n"
            "                }\n"
            "            }\n"
            "        }\n"
            "\n"
            "        // [claude-hwpx span-ladder-trust] 미뤄 둔"
        ),
    ),
    (
        "renderer/height_measurer.rs",
        "        // 3단계: 높이가 0인 행은 기본값 적용\n",
        (
            f"        // {TAG} HWPX 글자처럼 취급 표에 한 행 칸 없는 행이 있으면 위에서부터 차례로 정한다 — 행마다 한 행 칸 높이와 그 행에서 끝나는\n"
            "        // 병합 칸의 모자란 몫 중 큰 값. 2-b 가 내용보다 작은 병합 칸 선언으로 빈 행을 먼저 정해 부족분이 뒤 행에 쌓였다\n"
            "        // (결과보고서 163번 표 10행: 엔진 29.5px, 한/글 21.7px = 8~10행 칸 선언 - 8행 - 9행, 11행 글이 4px 아래)\n"
            "        if !self.is_native_hwp5 && !self.is_hwp3_variant && table.common.treat_as_char {\n"
            "            let claude_fixed: Vec<bool> = (0..row_count)\n"
            "                .map(|r| table.cells.iter().any(|c| c.row as usize == r && c.row_span == 1))\n"
            "                .collect();\n"
            "            if claude_fixed.iter().any(|f| !f) {\n"
            "                let shrink = table.rowspan_declared_overflow_shrink();\n"
            "                let mut h = vec![0.0f64; row_count];\n"
            "                for r in 0..row_count {\n"
            "                    let mut v = if claude_fixed[r] {\n"
            "                        let s = shrink.get(r).copied().unwrap_or(0);\n"
            "                        if s > 0 {\n"
            "                            (claude_h1[r] - hwpunit_to_px(s as i32, self.dpi)).max(content_row_floor[r])\n"
            "                        } else {\n"
            "                            claude_h1[r]\n"
            "                        }\n"
            "                    } else {\n"
            "                        0.0\n"
            "                    };\n"
            "                    for &(sr, span, req) in &claude_span_req {\n"
            "                        if sr + span - 1 == r {\n"
            "                            let before: f64 = h[sr..r].iter().sum();\n"
            "                            v = v.max(req - before);\n"
            "                        }\n"
            "                    }\n"
            "                    h[r] = v;\n"
            "                }\n"
            "                row_heights[..row_count].copy_from_slice(&h);\n"
            "            }\n"
            "        }\n"
            "        // 3단계: 높이가 0인 행은 기본값 적용\n"
        ),
    ),
]


def main():
    revert = "--revert" in sys.argv
    edits = list(reversed(EDITS)) if revert else EDITS
    for rel, find, repl in edits:
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
            sys.exit(f"{rel}: 자리 {n}곳 — {find[:60]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel)


if __name__ == "__main__":
    main()
