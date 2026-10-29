"""개발용: 칸 저장 줄을 차례로 쌓아 끝을 잴 때(tac-row-ladder, cell-floor-stack, span-ladder-trust) 같은 위치의 가로 조각 줄은 같은 줄로 보고,
줄 간격은 음수도 그대로 쓴다.

    python apply_ladder_stack_frag.py [--revert]

근거(정답본 d020 2번 문단 표, 한/글 표 높이 59500 = 칸 선언 합): 칸 1행 오른쪽 문단에 같은 vertpos(2468)의 가로 조각 줄이 둘 있고, 음수 줄 간격
(-392, -1040, -912, -1300)이 있다. 쌓기 셈이 둘째 조각을 한 줄 아래로 또 쌓고 음수 간격을 0 으로 바꿔 칸 끝을 부풀려, 열 때 다시 재기
(tac-restate-on-open)가 표를 61601 로 쟀다(+28px, d020 1 → 2쪽).
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx ladder-stack-frag]"

EDITS = [
    (
        "renderer/height_measurer.rs",
        (
            "                    let (mut next_top, mut end) = (0i32, 0i32);\n"
            "                    for s in c.paragraphs.iter().flat_map(|p| p.line_segs.iter()) {\n"
            "                        let top = s.vertical_pos.max(next_top);\n"
            "                        end = end.max(top.saturating_add(s.line_height));\n"
            "                        next_top = top.saturating_add(s.line_height).saturating_add(s.line_spacing.max(0));\n"
            "                    }\n"
        ),
        (
            "                    let (mut next_top, mut end) = (0i32, 0i32);\n"
            f"                    // {TAG} 같은 위치의 가로 조각 줄은 같은 줄, 줄 간격은 음수도 그대로(d020: 조각 2468 둘, 간격 -1040)\n"
            "                    let mut claude_prev: Option<(i32, i32)> = None;\n"
            "                    for s in c.paragraphs.iter().flat_map(|p| p.line_segs.iter()) {\n"
            "                        let frag = claude_prev.filter(|&(v, _)| v == s.vertical_pos);\n"
            "                        let top = frag.map(|(_, t)| t).unwrap_or_else(|| s.vertical_pos.max(next_top));\n"
            "                        end = end.max(top.saturating_add(s.line_height));\n"
            "                        let nt = top.saturating_add(s.line_height).saturating_add(s.line_spacing);\n"
            "                        next_top = if frag.is_some() { next_top.max(nt) } else { nt };\n"
            "                        claude_prev = Some((s.vertical_pos, top));\n"
            "                    }\n"
        ),
    ),
    (
        "renderer/height_measurer.rs",
        (
            "                    let (mut next_top, mut end) = (0i64, 0i64);\n"
            "                    for s in cell.paragraphs.iter().flat_map(|p| p.line_segs.iter()) {\n"
            "                        let top = i64::from(s.vertical_pos).max(next_top);\n"
            "                        end = end.max(top + i64::from(s.line_height));\n"
            "                        next_top = top + i64::from(s.line_height) + i64::from(s.line_spacing.max(0));\n"
            "                    }\n"
        ),
        (
            "                    let (mut next_top, mut end) = (0i64, 0i64);\n"
            f"                    // {TAG} 같은 위치의 가로 조각 줄은 같은 줄, 줄 간격은 음수도 그대로\n"
            "                    let mut claude_prev: Option<(i32, i64)> = None;\n"
            "                    for s in cell.paragraphs.iter().flat_map(|p| p.line_segs.iter()) {\n"
            "                        let frag = claude_prev.filter(|&(v, _)| v == s.vertical_pos);\n"
            "                        let top = frag.map(|(_, t)| t).unwrap_or_else(|| i64::from(s.vertical_pos).max(next_top));\n"
            "                        end = end.max(top + i64::from(s.line_height));\n"
            "                        let nt = top + i64::from(s.line_height) + i64::from(s.line_spacing);\n"
            "                        next_top = if frag.is_some() { next_top.max(nt) } else { nt };\n"
            "                        claude_prev = Some((s.vertical_pos, top));\n"
            "                    }\n"
        ),
    ),
    (
        "renderer/height_measurer.rs",
        (
            "                    let (mut next_top, mut end) = (0i64, 0i64);\n"
            "                    for seg in cell.paragraphs.iter().flat_map(|p| p.line_segs.iter()) {\n"
            "                        let top = i64::from(seg.vertical_pos).max(next_top);\n"
            "                        end = end.max(top + i64::from(seg.line_height));\n"
            "                        next_top = top + i64::from(seg.line_height) + i64::from(seg.line_spacing.max(0));\n"
            "                    }\n"
        ),
        (
            "                    let (mut next_top, mut end) = (0i64, 0i64);\n"
            f"                    // {TAG} 같은 위치의 가로 조각 줄은 같은 줄, 줄 간격은 음수도 그대로\n"
            "                    let mut claude_prev: Option<(i32, i64)> = None;\n"
            "                    for seg in cell.paragraphs.iter().flat_map(|p| p.line_segs.iter()) {\n"
            "                        let frag = claude_prev.filter(|&(v, _)| v == seg.vertical_pos);\n"
            "                        let top = frag.map(|(_, t)| t).unwrap_or_else(|| i64::from(seg.vertical_pos).max(next_top));\n"
            "                        end = end.max(top + i64::from(seg.line_height));\n"
            "                        let nt = top + i64::from(seg.line_height) + i64::from(seg.line_spacing);\n"
            "                        next_top = if frag.is_some() { next_top.max(nt) } else { nt };\n"
            "                        claude_prev = Some((seg.vertical_pos, top));\n"
            "                    }\n"
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
