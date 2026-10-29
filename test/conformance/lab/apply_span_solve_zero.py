"""개발용: 표 행 측정 두 가지(HWPX) — 병합 칸 선언 풀이에서 0 으로 풀린 행을 「아는 행」으로 두고, 칸 마지막 빈 앵커 문단의 그림 겹침은 줄 높이만 뺀다.

    python apply_span_solve_zero.py [--revert]

근거(정답본, 열 때 다시 재기 tac-restate-on-open 이 한/글과 다르게 잰 표):
  - d120 50번 예산표: 2-b 풀이가 행 높이 0 을 「아직 모름」으로 써서, 선언으로 0 이 된 10, 12행을 다시 모르는 행으로 보고 남은 높이를 고르게
    나눴다(10~12행 1124씩). 한/글은 0/2248/0 이고 행 합 29572 = 표 높이 29573. 엔진은 30696 으로 쟀다.
  - d347 47번 표: 그림만 든 칸(빈 문단 + 위아래 배치 그림 7474, 18462)을 「줄 14.7 + 그림 99.7 - 겹침 22.1」로 쟀다. 겹침이 줄 높이에 줄 간격까지
    더한 값인데, 칸 마지막 줄의 글 높이는 줄 간격을 빼고 센다(tac-no-shrink-hwpx). 한/글 행 = 그림 + 칸 여백(7756, 18744, 합이 표 높이와 같다).
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx span-solve-zero]"

EDITS = [
    (
        "renderer/height_measurer.rs",
        (
            "            constraints.sort_by_key(|&(_, span, _)| span);\n"
            "            let max_iter = row_count + constraints.len();\n"
            "            for _ in 0..max_iter {\n"
            "                let mut progress = false;\n"
            "                for &(r, span, total_h) in &constraints {\n"
            "                    let known_sum: f64 = (r..r + span).map(|i| row_heights[i]).sum();\n"
            "                    let unknown_rows: Vec<usize> =\n"
            "                        (r..r + span).filter(|&i| row_heights[i] == 0.0).collect();\n"
            "                    if unknown_rows.len() == 1 {\n"
            "                        let remaining = (total_h - known_sum).max(0.0);\n"
            "                        row_heights[unknown_rows[0]] = remaining;\n"
            "                        progress = true;\n"
            "                    }\n"
            "                }\n"
            "                if !progress {\n"
            "                    break;\n"
            "                }\n"
            "            }\n"
            "            for &(r, span, total_h) in &constraints {\n"
            "                let known_sum: f64 = (r..r + span).map(|i| row_heights[i]).sum();\n"
            "                let unknown_rows: Vec<usize> =\n"
            "                    (r..r + span).filter(|&i| row_heights[i] == 0.0).collect();\n"
        ),
        (
            "            constraints.sort_by_key(|&(_, span, _)| span);\n"
            f"            // {TAG} HWPX 는 선언으로 0 이 된 행도 「아는 행」이다 — 0 을 모름으로 쓰면 그 행을 다시 풀어 남은 높이를 고르게 나눴다(d120 10~12행)\n"
            "            let claude_hwpx = !self.is_native_hwp5 && !self.is_hwp3_variant;\n"
            "            let mut claude_known: Vec<bool> = row_heights.iter().map(|h| *h != 0.0).collect();\n"
            "            let max_iter = row_count + constraints.len();\n"
            "            for _ in 0..max_iter {\n"
            "                let mut progress = false;\n"
            "                for &(r, span, total_h) in &constraints {\n"
            "                    let known_sum: f64 = (r..r + span).map(|i| row_heights[i]).sum();\n"
            "                    let unknown_rows: Vec<usize> = (r..r + span)\n"
            "                        .filter(|&i| if claude_hwpx { !claude_known[i] } else { row_heights[i] == 0.0 })\n"
            "                        .collect();\n"
            "                    if unknown_rows.len() == 1 {\n"
            "                        let remaining = total_h - known_sum;\n"
            "                        // 음수로 풀리는(0 으로 깎이는) 행은 미룬다 — 다른 병합 칸이 양수로 정해 줄 수 있다(169번 표 16행: 한/글 277)\n"
            "                        if claude_hwpx && remaining < 0.0 {\n"
            "                            continue;\n"
            "                        }\n"
            "                        row_heights[unknown_rows[0]] = remaining.max(0.0);\n"
            "                        claude_known[unknown_rows[0]] = true;\n"
            "                        progress = true;\n"
            "                    }\n"
            "                }\n"
            "                // 양수로 더 못 풀면 음수로 풀리는 행 하나를 0 으로 확정하고 다시 푼다(d120 10행)\n"
            "                if !progress && claude_hwpx {\n"
            "                    for &(r, span, _) in &constraints {\n"
            "                        let unknown_rows: Vec<usize> = (r..r + span).filter(|&i| !claude_known[i]).collect();\n"
            "                        if unknown_rows.len() == 1 {\n"
            "                            row_heights[unknown_rows[0]] = 0.0;\n"
            "                            claude_known[unknown_rows[0]] = true;\n"
            "                            progress = true;\n"
            "                            break;\n"
            "                        }\n"
            "                    }\n"
            "                }\n"
            "                if !progress {\n"
            "                    break;\n"
            "                }\n"
            "            }\n"
            "            for &(r, span, total_h) in &constraints {\n"
            "                let known_sum: f64 = (r..r + span).map(|i| row_heights[i]).sum();\n"
            "                let unknown_rows: Vec<usize> = (r..r + span)\n"
            "                    .filter(|&i| if claude_hwpx { !claude_known[i] } else { row_heights[i] == 0.0 })\n"
            "                    .collect();\n"
        ),
    ),
    (
        "renderer/height_measurer.rs",
        (
            "    fn claude_empty_host_overlap(&self, paragraphs: &[Paragraph]) -> f64 {\n"
            "        paragraphs\n"
            "            .iter()\n"
            "            .map(|para| {\n"
        ),
        (
            "    fn claude_empty_host_overlap(&self, paragraphs: &[Paragraph]) -> f64 {\n"
            f"        // {TAG} 칸 마지막 문단은 글 높이에서 줄 간격을 빼고 세므로(HWPX) 겹침도 줄 높이만 뺀다(d347 47번 표: 그림 칸이 줄 간격만큼 작았다)\n"
            "        let claude_hwpx = !self.is_native_hwp5 && !self.is_hwp3_variant;\n"
            "        let last = paragraphs.len().saturating_sub(1);\n"
            "        paragraphs\n"
            "            .iter()\n"
            "            .enumerate()\n"
            "            .map(|(claude_i, para)| {\n"
            "                if claude_hwpx && claude_i == last {\n"
            "                    let flow = para\n"
            "                        .controls\n"
            "                        .iter()\n"
            "                        .map(|ctrl| match ctrl {\n"
            "                            Control::Picture(pic) => self.non_inline_control_flow_height(&pic.common),\n"
            "                            Control::Shape(shape) => self.non_inline_control_flow_height(shape.common()),\n"
            "                            _ => 0.0,\n"
            "                        })\n"
            "                        .fold(0.0f64, f64::max);\n"
            "                    let full = claude_empty_host_flow_overlap_px(para, flow, self.dpi);\n"
            "                    let lh = para.line_segs.first().map(|s| hwpunit_to_px(s.line_height, self.dpi)).unwrap_or(0.0);\n"
            "                    return full.min(lh);\n"
            "                }\n"
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
