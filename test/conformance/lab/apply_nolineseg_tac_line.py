"""개발용: 줄 배치 없는 표 다시 재기(nolineseg-table-restate)가 글자처럼 취급 표면 엔진이 만든 품은 줄 높이도 새 표 높이 + 바깥 여백으로 고친다.

    python apply_nolineseg_tac_line.py [--revert]

근거(회귀 모음 「실습지」 c15, 스킬 생성기 더미 줄 배치를 걷은 사본 = 에디터가 실제로 여는 모양): 1×1 글자처럼 취급 상자 표(적힌 1565,
칸 글 세 줄 = 59.8px)를 다시 재 표 높이는 고쳤는데, 열 때 엔진이 만든 품은 줄은 옛 높이(20.9 + 여백 = 27.5px)로 남아 쪽 나누기가
상자를 27.5px 로 셌다. 그래서 1쪽에 상자 다섯 줄과 다음 제목까지 담아 용지 밖(1094px)으로 넘쳤다(한/글 4쪽, 엔진 3쪽).
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx nolineseg-tac-line]"

EDITS = [
    (
        "document_core/commands/document.rs",
        "            let mut first: Vec<Option<usize>> = vec![None; doc.document.sections.len()];\n",
        (
            f"            // {TAG} 문서 단위 판정: 재 본 높이가 적힌 높이와 25% 넘게 다른 표가 있으면 적힌 높이가 생성기 어림값인 문서다. 줄 배치만 지운 한/글\n"
            "            // 저장본은 적힌 높이가 맞으니 품은 줄을 건드리지 않는다(엔진 측정으로 바꾸면 정답본 쪽수 100 → 97.6%)\n"
            "            let claude_estimated_doc = targets.iter().any(|&(si, pi, ci)| {\n"
            "                let p = &doc.document.sections[si].paragraphs[pi];\n"
            "                let Some(Control::Table(t)) = p.controls.get(ci) else {\n"
            "                    return false;\n"
            "                };\n"
            "                let px = crate::renderer::height_measurer::HeightMeasurer::new(doc.dpi)\n"
            "                    .measure_table_for_edit(t, pi, ci, &doc.styles);\n"
            "                let (new_h, old) = (crate::renderer::px_to_hwpunit(px, doc.dpi), t.common.height as i32);\n"
            "                (new_h - old).abs() * 4 > old\n"
            "            });\n"
            "            let mut first: Vec<Option<usize>> = vec![None; doc.document.sections.len()];\n"
        ),
    ),
    (
        "document_core/commands/document.rs",
        (
            "                if new_h <= 0 || (new_h - t.common.height as i32).abs() < 75 {\n"
            "                    continue;\n"
            "                }\n"
            "                t.common.height = new_h as u32;\n"
            "                doc.recompose_paragraph(si, pi);\n"
        ),
        (
            "                if new_h <= 0 || (new_h - t.common.height as i32).abs() < 75 {\n"
            "                    continue;\n"
            "                }\n"
            f"                // {TAG} 글자처럼 취급 표면 열 때 만든 품은 줄(옛 표 높이 + 여백)도 고친다(c15 상자: 줄 27.5px 로 남아 쪽 나누기가 작게 셌다)\n"
            "                let claude_old = t.common.height as i32;\n"
            "                let claude_tac = t.common.treat_as_char;\n"
            "                let claude_outer = t.outer_margin_top as i32 + t.outer_margin_bottom as i32;\n"
            "                t.common.height = new_h as u32;\n"
            "                if claude_tac && claude_estimated_doc {\n"
            "                    if let Some(seg) = p\n"
            "                        .line_segs\n"
            "                        .iter_mut()\n"
            "                        .find(|s| (s.line_height - (claude_old + claude_outer)).abs() <= 75)\n"
            "                    {\n"
            "                        let new_lh = new_h + claude_outer;\n"
            "                        if seg.line_height > 0 {\n"
            "                            seg.baseline_distance =\n"
            "                                (seg.baseline_distance as i64 * new_lh as i64 / seg.line_height as i64) as i32;\n"
            "                        }\n"
            "                        seg.line_height = new_lh;\n"
            "                        seg.text_height = new_lh;\n"
            "                    }\n"
            "                }\n"
            "                doc.recompose_paragraph(si, pi);\n"
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
