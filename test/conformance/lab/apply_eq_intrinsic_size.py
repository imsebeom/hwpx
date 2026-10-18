"""개발용: 줄 배치가 없는 문단의 글자처럼 취급 수식은 스크립트로 잰 크기가 적힌 높이보다 크면 그 크기로 바로잡는다.

    python apply_eq_intrinsic_size.py [--revert]

근거(2026-10-18 빌더 다리 시험): 스킬 add_equation.py 는 수식 크기를 어림값(분수 수식도 폭 11,040, 높이 1,020)으로 적는다.
한/글은 그릴 때 스크립트로 다시 재 칸이 늘었는데(한/글 PDF), 엔진은 적힌 높이로 줄 높이를 잡아 표 칸 안 분수 수식이 잘렸다.
에디터 자체의 수식 넣기(insertEquation)는 intrinsic_size_hwp 로 잰다. 저장된 줄 배치가 있는 문단(한/글 저장본)은 건드리지 않는다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx eq-intrinsic-size]"

EDITS = [
    (
        "document_core/commands/document.rs",
        "        Self::reflow_zero_height_paragraphs(\n",
        f"        // {TAG} 줄 배치 없는 문단(빌더, 도구 산출물)의 글자처럼 취급 수식은 스크립트로 잰 크기가 적힌 높이보다 크면 그 크기로\n"
        "        // (빌더는 어림 크기를 적는다. 한/글은 그릴 때 다시 잰다). 줄 배치가 있는 문단은 한/글이 잰 줄 높이를 믿는다\n"
        "        fn claude_fix_equation_sizes(paras: &mut [crate::model::paragraph::Paragraph]) {\n"
        "            for p in paras.iter_mut() {\n"
        "                let no_lines = p.line_segs.is_empty();\n"
        "                for c in p.controls.iter_mut() {\n"
        "                    match c {\n"
        "                        crate::model::control::Control::Equation(eq) if no_lines && eq.common.treat_as_char && !eq.script.is_empty() => {\n"
        "                            let (w, h) = crate::renderer::equation::intrinsic_size_hwp(&eq.script, eq.font_size);\n"
        "                            if h > eq.common.height {\n"
        "                                eq.common.height = h;\n"
        "                                eq.common.width = w;\n"
        "                            }\n"
        "                        }\n"
        "                        crate::model::control::Control::Table(t) => {\n"
        "                            for cell in t.cells.iter_mut() {\n"
        "                                claude_fix_equation_sizes(&mut cell.paragraphs);\n"
        "                            }\n"
        "                        }\n"
        "                        _ => {}\n"
        "                    }\n"
        "                }\n"
        "            }\n"
        "        }\n"
        "        for section in document.sections.iter_mut() {\n"
        "            claude_fix_equation_sizes(&mut section.paragraphs);\n"
        "        }\n"
        "        Self::reflow_zero_height_paragraphs(\n",
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
