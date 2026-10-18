"""개발용: HWPX 를 불러올 때 줄 배치가 없는 각주 문단(본문 문단과 표 칸 안 각주 모두)도 줄을 만든다.

    python apply_footnote_reflow.py [--revert]

근거(2026-10-18 가이드북 2장 원고 _44, 사용자 화면): 스크립트로 넣은 각주는 줄 배치(linesegarray)가 없다. 각주 높이 추정
(estimate_footnote_note_height)은 줄 배치 없는 문단을 400 HU(5.3px)로 세어, 6쪽 표(4x3, 칸 안 각주 4개, 각 2줄)의 각주를
21px 로 잡고 표와 캡션을 쪽 아래까지 앉혔다. 그려지는 각주는 약 125px 라 표 아래쪽과 캡션 위에 겹쳤다. 본문과 표 캡션 문단은
불러올 때 이미 줄을 만드니(reflow_zero_height_paragraphs) 같은 자리에서 각주 문단도 단 폭과 그 문단 여백으로 줄을 만든다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx footnote-reflow]"

EDITS = [
    (
        "document_core/commands/document.rs",
        "                // [claude-hwpx tac-caption-line] 표 캡션 문단도 줄 배치가 없으면 먼저 조판한다.",
        f"                // {TAG} 줄 배치 없는 각주 문단(표 칸 안 포함)도 줄을 만든다. 없으면 각주 높이를 문단당 400 HU 로 세어\n"
        "                // 표와 본문이 각주 자리까지 내려와 겹친다(가이드북 2장 표 2-11)\n"
        "                if include_empty {\n"
        "                    fn claude_reflow_notes(\n"
        "                        ctrls: &mut [Control],\n"
        "                        col_width: f64,\n"
        "                        styles: &ResolvedStyleSet,\n"
        "                        dpi: f64,\n"
        "                    ) {\n"
        "                        for ctrl in ctrls.iter_mut() {\n"
        "                            let notes = match ctrl {\n"
        "                                Control::Footnote(f) => Some(&mut f.paragraphs),\n"
        "                                Control::Endnote(e) => Some(&mut e.paragraphs),\n"
        "                                Control::Table(t) => {\n"
        "                                    for cell in t.cells.iter_mut() {\n"
        "                                        for cp in cell.paragraphs.iter_mut() {\n"
        "                                            claude_reflow_notes(&mut cp.controls, col_width, styles, dpi);\n"
        "                                        }\n"
        "                                    }\n"
        "                                    None\n"
        "                                }\n"
        "                                _ => None,\n"
        "                            };\n"
        "                            for fp in notes.into_iter().flatten() {\n"
        "                                if fp.line_segs.is_empty() {\n"
        "                                    let st = styles.para_styles.get(fp.para_shape_id as usize);\n"
        "                                    reflow_line_segs(fp, ParagraphBox::body_for_style(col_width, st, dpi), styles, dpi);\n"
        "                                }\n"
        "                            }\n"
        "                        }\n"
        "                    }\n"
        "                    claude_reflow_notes(&mut para.controls, col_width, styles, dpi);\n"
        "                }\n"
        "                // [claude-hwpx tac-caption-line] 표 캡션 문단도 줄 배치가 없으면 먼저 조판한다.",
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
