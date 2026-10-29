"""개발용: 에디터(rhwp)가 저장한 HWPX 구역은 열 때 표만 든 문단의 글자처럼 취급 표 높이와 호스트 줄을 다시 잰다.

    python apply_rhwp_saved_tac_restate.py [--revert]

근거(2026-10-29 결과보고서 21:27 판, 에디터 저장본): 설문 표 88~91번의 표 높이와 호스트 줄이 옛 엔진이 잰 값(88번 15720 = 209.6px,
고치기 전 칸 마지막 줄 간격 포함)으로 적혀 있다. 한/글은 열 때 표 높이를 행 내용으로 다시 재서 15186(202.5px)으로 그린다. 엔진은 이제
202.4px 로 맞게 재지만 조판이 저장 줄 높이를 써서 표마다 7.2px 컸다(13, 14쪽 글줄 ±7px). 한/글이 저장한 문서는 줄 위치가 쪽마다 0으로
돌아가 본문 높이(약 67,000)를 넘지 않는다 — 100,000 을 넘는 줄 위치가 있는 구역만 에디터 저장본으로 보고 다시 잰다.
저장 줄이 선언 높이를 그대로 옮긴 경우(차이 1px 안, 엔진이 쓴 값)만 고친다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx rhwp-saved-tac-restate]"

EDITS = [
    (
        "document_core/commands/document.rs",
        "            doc.claude_renumber_notes();\n        }\n        doc.rebuild_embedded_exact_font_sources();\n",
        (
            "            doc.claude_renumber_notes();\n"
            "        }\n"
            f"        // {TAG} 에디터가 저장한 구역(줄 위치가 쪽마다 0으로 돌아가지 않아 100,000 을 넘음)은 표 높이와 호스트 줄이 옛 엔진이 잰 값이다.\n"
            "        // 한/글은 열 때 글자처럼 취급 표 높이를 행 내용으로 다시 잰다(결과보고서 88번 표: 적힌 15720, 한/글 15186)\n"
            "        if matches!(doc.source_format, crate::parser::FileFormat::Hwpx) {\n"
            "            use crate::model::control::Control;\n"
            "            let mut targets = Vec::new();\n"
            "            for (si, sec) in doc.document.sections.iter().enumerate() {\n"
            "                let rhwp_ladder = sec\n"
            "                    .paragraphs\n"
            "                    .iter()\n"
            "                    .any(|p| p.line_segs.first().is_some_and(|s| s.vertical_pos > 100_000));\n"
            "                if !rhwp_ladder {\n"
            "                    continue;\n"
            "                }\n"
            "                for (pi, p) in sec.paragraphs.iter().enumerate() {\n"
            "                    let tacs: Vec<usize> = p\n"
            "                        .controls\n"
            "                        .iter()\n"
            "                        .enumerate()\n"
            "                        .filter(|(_, c)| matches!(c, Control::Table(t) if t.common.treat_as_char))\n"
            "                        .map(|(i, _)| i)\n"
            "                        .collect();\n"
            "                    if tacs.len() != 1\n"
            "                        || p.line_segs.len() != 1\n"
            "                        || !p.text.chars().all(|c| c.is_whitespace() || c.is_control())\n"
            "                    {\n"
            "                        continue;\n"
            "                    }\n"
            "                    let Some(Control::Table(t)) = p.controls.get(tacs[0]) else {\n"
            "                        continue;\n"
            "                    };\n"
            "                    let outer = t.outer_margin_top as i32 + t.outer_margin_bottom as i32;\n"
            "                    if t.caption.is_some()\n"
            "                        || (p.line_segs[0].line_height - (t.common.height as i32 + outer)).abs() > 75\n"
            "                    {\n"
            "                        continue;\n"
            "                    }\n"
            "                    targets.push((si, pi, tacs[0]));\n"
            "                }\n"
            "            }\n"
            "            for (si, pi, ci) in targets {\n"
            "                let (new_h, old_end) = {\n"
            "                    let p = &doc.document.sections[si].paragraphs[pi];\n"
            "                    let Some(Control::Table(t)) = p.controls.get(ci) else {\n"
            "                        continue;\n"
            "                    };\n"
            "                    (doc.claude_raw_table_measure(t, pi, ci), crate::renderer::composer::paragraph_flow_end(p))\n"
            "                };\n"
            "                let p = &mut doc.document.sections[si].paragraphs[pi];\n"
            "                let Some(Control::Table(t)) = p.controls.get_mut(ci) else {\n"
            "                    continue;\n"
            "                };\n"
            "                let old_h = t.common.height as i32;\n"
            "                if new_h <= 0 || (new_h - old_h).abs() < 75 {\n"
            "                    continue;\n"
            "                }\n"
            "                let outer = t.outer_margin_top as i32 + t.outer_margin_bottom as i32;\n"
            "                t.common.height = new_h as u32;\n"
            "                let seg = &mut p.line_segs[0];\n"
            "                let new_lh = new_h + outer;\n"
            "                if seg.line_height > 0 {\n"
            "                    seg.baseline_distance = (seg.baseline_distance as i64 * new_lh as i64 / seg.line_height as i64) as i32;\n"
            "                }\n"
            "                seg.line_height = new_lh;\n"
            "                seg.text_height = new_lh;\n"
            "                doc.claude_shift_following_vpos(si, pi, old_end);\n"
            "            }\n"
            "        }\n"
            "        doc.rebuild_embedded_exact_font_sources();\n"
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
