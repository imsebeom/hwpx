"""개발용: 줄 배치가 없는 칸의 어울림 그림 옆으로 글을 흘린다(본문 load-picture-band 와 같은 계산).

    python apply_cell_picture_band.py [--revert]

근거(회귀 c70 문항카드, 2쪽 자료 1, 자료 2): 줄 배치 없는 칸의 오른쪽 어울림 그림 위로 글이 칸 폭으로 펼쳐져 겹쳤다. 한/글은 그림 옆에서 줄을 나눈다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx cell-picture-band]"

A1 = "/// [claude-hwpx load-picture-band] 열 때 합성 줄을 띠로 짤 때는"
FN = f"""/// {TAG} 줄 배치를 합성한 칸(표 속 표 포함)의 어울림 그림 옆 문단을 그림 띠 줄로 바꾼다.
pub(crate) fn claude_cell_picture_bands(paras: &mut [Paragraph], styles: &ResolvedStyleSet, dpi: f64) {{
    for para in paras.iter_mut() {{
        for ctrl in para.controls.iter_mut() {{
            let Control::Table(table) = ctrl else {{
                continue;
            }};
            let owner_widths = table.paragraph_frame_owner_widths();
            let table_padding = table.padding;
            for (cell, owner_width) in table.cells.iter_mut().zip(owner_widths) {{
                claude_cell_picture_bands(&mut cell.paragraphs, styles, dpi);
                let synth = |p: &Paragraph| p.line_segs.iter().all(|s| s.tag & LineSeg::TAG_IMPLEMENTATION_PROPERTY != 0);
                if !cell.paragraphs.iter().all(synth) {{
                    continue;
                }}
                let padding = cell.paragraph_frame_padding(&table_padding);
                let inner = crate::renderer::composer::cell_inner_text_width(
                    crate::renderer::hwpunit_to_px(owner_width, dpi),
                    crate::renderer::hwpunit_to_px(padding.left as i32, dpi),
                    crate::renderer::hwpunit_to_px(padding.right as i32, dpi),
                    dpi,
                );
                let mut hi = 0usize;
                while hi < cell.paragraphs.len() {{
                    let is_host = cell.paragraphs[hi].controls.iter().any(|c| {{
                        matches!(c, Control::Picture(p) if !p.common.treat_as_char
                            && p.common.text_wrap == crate::model::shape::TextWrap::Square)
                    }});
                    let band = is_host
                        .then(|| claude_layout_picture_band_to_doc_end(&cell.paragraphs, hi, inner, styles, dpi))
                        .flatten();
                    let Some(band) = band else {{
                        hi += 1;
                        continue;
                    }};
                    let range = band.paragraph_range.clone();
                    for (pi, segs) in range.clone().zip(band.line_segs) {{
                        cell.paragraphs[pi].replace_line_segs(segs);
                    }}
                    hi = range.end.max(hi + 1);
                }}
            }}
        }}
    }}
}}

"""
A2 = "            // [claude-hwpx load-picture-band] 줄 배치를 합성한 문단이 어울림(Square) 그림 옆에"
CALL = f"            // {TAG}\n            crate::renderer::composer::claude_cell_picture_bands(&mut section.paragraphs, styles, dpi);\n\n"
E1 = "pub(crate) use line_breaking::claude_repair_line_head_flags;\n"

EDITS = [
    ("renderer/composer/line_breaking.rs", A1, FN + A1),
    (
        "renderer/composer.rs",
        E1,
        E1 + f"// {TAG}\npub(crate) use line_breaking::claude_cell_picture_bands;\n",
    ),
    ("document_core/commands/document.rs", A2, CALL + A2),
]


def main():
    revert = "--revert" in sys.argv
    edits = list(reversed(EDITS)) if revert else EDITS
    for rel, find, repl in edits:
        p = SRC / rel
        raw = p.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        s = raw.replace("\r\n", "\n")
        a, b = (repl, find) if revert else (find, repl)
        assert s.count(a) == 1, (rel, a[:70], s.count(a))
        p.write_bytes(s.replace(a, b).replace("\n", nl).encode("utf-8"))
    print("되돌림" if revert else "적용")


if __name__ == "__main__":
    main()
