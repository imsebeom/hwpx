"""개발용: HWPX 를 열 때 각주, 미주 번호를 문서 순서대로 다시 매긴다(저장된 number 값을 믿지 않는다).

    python apply_note_renumber_load.py [--revert]

교사개발자 가이드북 파트2 합본: 합칠 때 16번째 각주(백엔드)가 number="1" 로 저장돼 그 뒤 각주의 number 가 하나씩 작다.
한/글은 저장 값을 무시하고 순서대로 매겨 16), 72) 로 그리는데(한/글 PDF 19쪽 「16) 백엔드」, 59쪽 「72) 프론트엔드 코드」)
엔진은 저장 값 그대로 1), 71) 로 그렸다. 편집 뒤에 쓰던 claude_renumber_notes(note-renumber)를 문서를 열 때도 부른다.
그 함수는 「새 번호로 시작」 컨트롤을 모르므로 각주, 미주 새 번호 컨트롤이 있는 문서는 건드리지 않는다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx note-renumber-load]"

EDITS = [
    (
        "document_core/commands/document.rs",
        "        doc.rebuild_embedded_exact_font_sources();\n"
        "        doc.recompose_all_with_horizontal_shaping();\n"
        "        doc.paginate();\n",
        f"        // {TAG} 한/글은 각주, 미주의 저장 번호를 무시하고 문서 순서대로 매긴다(가이드북 파트2 합본 16번째 각주 number=1, 한/글 PDF 16)).\n"
        "        // 새 번호 컨트롤이 있으면 claude_renumber_notes 가 그것을 모르므로 그대로 둔다\n"
        "        fn claude_has_note_newnum(paras: &[crate::model::paragraph::Paragraph], depth: usize) -> bool {\n"
        "            use crate::model::control::{AutoNumberType, Control};\n"
        "            depth <= 8\n"
        "                && paras.iter().any(|p| {\n"
        "                    p.controls.iter().any(|c| match c {\n"
        "                        Control::NewNumber(n) => {\n"
        "                            matches!(n.number_type, AutoNumberType::Footnote | AutoNumberType::Endnote)\n"
        "                        }\n"
        "                        Control::Table(t) => t.cells.iter().any(|cell| claude_has_note_newnum(&cell.paragraphs, depth + 1)),\n"
        "                        Control::Shape(s) => s\n"
        "                            .drawing()\n"
        "                            .and_then(|d| d.text_box.as_ref())\n"
        "                            .is_some_and(|tb| claude_has_note_newnum(&tb.paragraphs, depth + 1)),\n"
        "                        _ => false,\n"
        "                    })\n"
        "                })\n"
        "        }\n"
        "        if matches!(doc.source_format, crate::parser::FileFormat::Hwpx)\n"
        "            && !doc.document.sections.iter().any(|s| claude_has_note_newnum(&s.paragraphs, 0))\n"
        "        {\n"
        "            doc.claude_renumber_notes();\n"
        "        }\n"
        "        doc.rebuild_embedded_exact_font_sources();\n"
        "        doc.recompose_all_with_horizontal_shaping();\n"
        "        doc.paginate();\n",
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
