"""개발용: 줄 배치가 하나도 없는 HWPX 표(칸 문단과 표를 품은 문단 모두)는 열 때 표 높이(sz)를 칸 내용으로 다시 재서 적는다.

    python apply_nolineseg_table_restate.py [--revert]

근거(교육력제고 결과보고서 「운영현황_중광초.hwpx」, 생성 스크립트 산출물): 표 sz 높이가 어림값이다(1번 표 48436 = 649.6px, 칸 높이는 1000씩,
5번 표 14706). 한/글은 줄 배치가 없으니 열 때 표를 내용으로 다시 재 2쪽으로 그린다. 엔진은 행은 내용대로(1번 표 337.9px) 그리면서 쪽 흐름은
적힌 높이로 잡아, 큰 표 뒤에 빈칸이 생기고(「4. 연수 참여 현황」이 1쪽 바닥 913px) 작게 적힌 표는 다음 표와 겹쳤다(3쪽).
한/글이 저장한 문서는 늘 줄 배치가 있어 대상이 아니다. 높이를 고친 뒤 그 문단부터 구역 줄 위치를 다시 계산한다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx nolineseg-table-restate]"

EDITS = [
    (
        "document_core/commands/document.rs",
        (
            "                doc.claude_shift_following_vpos(si, pi, old_end);\n"
            "                doc.recompose_paragraph(si, pi);\n"
            "            }\n"
            "        }\n"
            "        doc.paginate();\n"
        ),
        (
            "                doc.claude_shift_following_vpos(si, pi, old_end);\n"
            "                doc.recompose_paragraph(si, pi);\n"
            "            }\n"
            "        }\n"
            f"        // {TAG} 줄 배치가 하나도 없는 HWPX 표(칸 문단과 표를 품은 문단 모두)는 적힌 sz 높이가 생성기 어림값이다 — 한/글처럼\n"
            "        // 열 때 칸 내용으로 다시 잰다(운영현황 1번 표: 적힌 649.6px, 내용 337.9px. 엔진은 행은 내용대로 그리고 쪽 흐름은 적힌 높이로 잡아\n"
            "        // 표 뒤가 비거나 다음 표와 겹쳤다). 한/글 저장본은 줄 배치가 있어 대상이 아니다\n"
            "        if matches!(doc.source_format, crate::parser::FileFormat::Hwpx) {\n"
            "            use crate::model::control::Control;\n"
            "            let mut targets = Vec::new();\n"
            "            for (si, sec) in doc.document.sections.iter().enumerate() {\n"
            "                for (pi, p) in sec.paragraphs.iter().enumerate() {\n"
            "                    if !crate::renderer::para_has_no_stored_line_segs(p) {\n"
            "                        continue;\n"
            "                    }\n"
            "                    for (ci, c) in p.controls.iter().enumerate() {\n"
            "                        if let Control::Table(t) = c {\n"
            "                            if t.caption.is_none()\n"
            "                                && !t.cells.is_empty()\n"
            "                                && t.cells.iter().all(|cell| {\n"
            "                                    cell.paragraphs.iter().all(crate::renderer::para_has_no_stored_line_segs)\n"
            "                                })\n"
            "                            {\n"
            "                                targets.push((si, pi, ci));\n"
            "                            }\n"
            "                        }\n"
            "                    }\n"
            "                }\n"
            "            }\n"
            "            let mut first: Vec<Option<usize>> = vec![None; doc.document.sections.len()];\n"
            "            for (si, pi, ci) in targets {\n"
            "                let new_h = {\n"
            "                    let p = &doc.document.sections[si].paragraphs[pi];\n"
            "                    let Some(Control::Table(t)) = p.controls.get(ci) else {\n"
            "                        continue;\n"
            "                    };\n"
            "                    let px = crate::renderer::height_measurer::HeightMeasurer::new(doc.dpi)\n"
            "                        .measure_table_for_edit(t, pi, ci, &doc.styles);\n"
            "                    crate::renderer::px_to_hwpunit(px, doc.dpi)\n"
            "                };\n"
            "                let p = &mut doc.document.sections[si].paragraphs[pi];\n"
            "                let Some(Control::Table(t)) = p.controls.get_mut(ci) else {\n"
            "                    continue;\n"
            "                };\n"
            "                if new_h <= 0 || (new_h - t.common.height as i32).abs() < 75 {\n"
            "                    continue;\n"
            "                }\n"
            "                t.common.height = new_h as u32;\n"
            "                doc.recompose_paragraph(si, pi);\n"
            "                first[si] = Some(first[si].map_or(pi, |f| f.min(pi)));\n"
            "            }\n"
            "            for (si, f) in first.into_iter().enumerate() {\n"
            "                if let Some(pi) = f {\n"
            "                    doc.claude_shift_following_vpos(si, pi, None);\n"
            "                }\n"
            "            }\n"
            "        }\n"
            "        doc.paginate();\n"
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
