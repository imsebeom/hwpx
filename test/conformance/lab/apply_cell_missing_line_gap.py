"""개발용: HWPX 칸 안 이웃 문단 사이의 「빠진 줄」 간격(문단 간격 설정을 뺀 나머지가 앞 문단 마지막 줄 분량의 정수배)을 열 때 닫는다.

    python apply_cell_missing_line_gap.py [--revert]

근거(결과보고서 19:46 판 33쪽, 에디터 저장본): 칸(세로 가운데) 문단 넷이 모두 한 줄인데 둘째 문단 뒤 셋째 문단이 한 줄(1172 = 줄 900 +
간격 272) 아래에 적혀 있다(줄이 둘이던 때의 위치가 남음). 한/글은 열 때 이 간격을 닫고 네 줄로 가운데 맞춰, 엔진(다섯 줄로 봄)보다
글이 7.8px 아래다. 한/글이 다시 저장한 정답본 327개에도 설명 안 되는 칸 간격이 13곳 있지만 하나도 줄 분량의 정수배가 아니다
(568, 584, 780, 1455 등). 앞뒤 문단에 개체가 있으면(개체에 밀린 줄) 건드리지 않는다. 다시 재기(tac-restate-on-open) 앞에 둔다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx cell-missing-line-gap]"

EDITS = [
    (
        "document_core/commands/document.rs",
        "        // [claude-hwpx tac-restate-on-open] 한/글처럼 열 때",
        (
            f"        // {TAG} 칸 안 이웃 문단 사이 간격에서 문단 간격 설정을 뺀 나머지가 앞 문단 마지막 줄 분량의 정수배면 빠진 줄의 흔적이다\n"
            "        // (에디터 저장본: 줄이 줄어든 뒤 뒤 문단 위치가 남음). 한/글은 열 때 닫는다(결과보고서 33쪽 가운데 칸 7.8px). 한/글 저장본의\n"
            "        // 설명 안 되는 칸 간격(정답본 13곳)은 줄 분량의 정수배가 아니다. 개체가 든 문단은 건드리지 않는다\n"
            "        if matches!(doc.source_format, crate::parser::FileFormat::Hwpx) {\n"
            "            use crate::model::control::Control;\n"
            "            fn claude_close_cell_gaps(\n"
            "                t: &mut crate::model::table::Table,\n"
            "                styles: &crate::renderer::style_resolver::ResolvedStyleSet,\n"
            "                dpi: f64,\n"
            "            ) {\n"
            "                let plain = |p: &crate::model::paragraph::Paragraph| {\n"
            "                    p.controls.iter().all(|c| {\n"
            "                        !matches!(c, Control::Picture(_) | Control::Shape(_) | Control::Table(_) | Control::Equation(_))\n"
            "                    })\n"
            "                };\n"
            "                let sp = |id: u16, after: bool| {\n"
            "                    styles\n"
            "                        .para_styles\n"
            "                        .get(id as usize)\n"
            "                        .map(|s| crate::renderer::px_to_hwpunit(if after { s.spacing_after } else { s.spacing_before }, dpi))\n"
            "                        .unwrap_or(0)\n"
            "                };\n"
            "                for cell in &mut t.cells {\n"
            "                    let mut shift = 0i32;\n"
            "                    let n = cell.paragraphs.len();\n"
            "                    for i in 0..n {\n"
            "                        if shift != 0 {\n"
            "                            for s in &mut cell.paragraphs[i].line_segs {\n"
            "                                s.vertical_pos = s.vertical_pos.saturating_sub(shift);\n"
            "                            }\n"
            "                        }\n"
            "                        if i + 1 >= n {\n"
            "                            continue;\n"
            "                        }\n"
            "                        let (a, b) = (&cell.paragraphs[i], &cell.paragraphs[i + 1]);\n"
            "                        if !plain(a) || !plain(b) {\n"
            "                            continue;\n"
            "                        }\n"
            "                        let (Some(la), Some(fb)) = (a.line_segs.last(), b.line_segs.first()) else {\n"
            "                            continue;\n"
            "                        };\n"
            "                        if la.tag & 0x8000_0000 != 0 || fb.tag & 0x8000_0000 != 0 {\n"
            "                            continue;\n"
            "                        }\n"
            "                        let adv = la.line_height.saturating_add(la.line_spacing);\n"
            "                        let gap = fb.vertical_pos.saturating_sub(shift)\n"
            "                            - la.vertical_pos.saturating_add(adv)\n"
            "                            - sp(a.para_shape_id, true)\n"
            "                            - sp(b.para_shape_id, false);\n"
            "                        if adv > 0 && gap >= adv - 4 {\n"
            "                            let k = (gap + adv / 2) / adv;\n"
            "                            if (gap - k * adv).abs() <= 4 {\n"
            "                                shift = shift.saturating_add(gap);\n"
            "                            }\n"
            "                        }\n"
            "                    }\n"
            "                    for p in &mut cell.paragraphs {\n"
            "                        for c in &mut p.controls {\n"
            "                            if let Control::Table(nt) = c {\n"
            "                                claude_close_cell_gaps(nt, styles, dpi);\n"
            "                            }\n"
            "                        }\n"
            "                    }\n"
            "                }\n"
            "            }\n"
            "            let dpi = doc.dpi;\n"
            "            for sec in &mut doc.document.sections {\n"
            "                for p in &mut sec.paragraphs {\n"
            "                    for c in &mut p.controls {\n"
            "                        if let Control::Table(t) = c {\n"
            "                            claude_close_cell_gaps(t, &doc.styles, dpi);\n"
            "                        }\n"
            "                    }\n"
            "                }\n"
            "            }\n"
            "        }\n"
            "        // [claude-hwpx tac-restate-on-open] 한/글처럼 열 때"
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
