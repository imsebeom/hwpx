"""개발용: 줄을 다시 나눌 때 글머리, 내어쓰기 비트(flags 21, 20)를 한/글 규칙대로 쓴다. 저장본의 어긋난 비트는 열 때 고친다.

    python apply_line_head_flags.py [--revert]

근거(2026-10-30 다른 세션 보고, 문항 _10 채점 기준표): 칸 너비를 바꾸거나 글을 고치면 첫 줄 비트를 모든 줄에 복사해,
한/글이 글머리표를 줄바꿈된 줄에 붙이거나 빼고 내어쓰기를 잃었다. 비트만 고치면 글머리표 위치가 돌아오고, 내어쓰기 비트까지 맞아야 줄 정보를 지운 판과 같다.
규칙(한/글 새 조판 정답본 327개): 머리 문단은 첫 줄 비트 21(1198/1198), 둘째 줄부터 비트 21 없음(559/559)과 비트 20(436/441),
머리 없는 내어쓰기는 둘째 줄부터 비트 20(2741/2750), 들여쓰기는 첫 줄 비트 20(27/27), 여백 없는 문단은 없음(10955/10955).
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx line-head-flags]"
LB = "renderer/composer/line_breaking.rs"

SIG = (
    "fn reflow_line_segs_impl(\n"
    "    para: &mut Paragraph,\n"
    "    paragraph_box: ParagraphBox,\n"
    "    styles: &ResolvedStyleSet,\n"
    "    dpi: f64,\n"
    "    preserve_prefix_for_edit: Option<usize>,\n"
    "    split_stale_cell_reflow: bool,\n"
    ") -> bool {\n"
)

NEW = f"""/// {TAG} 줄마다 글머리(비트 21), 내어쓰기(비트 20) 비트를 한/글 규칙대로 쓴다.
fn claude_set_line_head_flags(para: &mut Paragraph, styles: &ResolvedStyleSet) {{
    let Some(st) = styles.para_styles.get(para.para_shape_id as usize) else {{
        return;
    }};
    let head = st.head_type != crate::model::style::HeadType::None;
    let indent = st.indent;
    for (i, seg) in para.line_segs.iter_mut().enumerate() {{
        seg.tag &= !(LineSeg::TAG_PARAGRAPH_HEAD | LineSeg::TAG_INDENTATION);
        if head {{
            seg.tag |= if i == 0 {{ LineSeg::TAG_PARAGRAPH_HEAD }} else {{ LineSeg::TAG_INDENTATION }};
        }} else if (indent < 0.0 && i > 0) || (indent > 0.0 && i == 0) {{
            seg.tag |= LineSeg::TAG_INDENTATION;
        }}
    }}
}}

/// {TAG} 열 때: 글머리 비트가 규칙과 어긋난 문단만 고친다. 한/글 저장본에는 이런 문단이 없다(정답본 1757줄 예외 0).
/// 옛 에디터 저장본을 다시 저장해도 글머리표가 어긋나지 않게 한다.
pub(crate) fn claude_repair_line_head_flags(paras: &mut [Paragraph], styles: &ResolvedStyleSet) {{
    for para in paras.iter_mut() {{
        let head = styles
            .para_styles
            .get(para.para_shape_id as usize)
            .is_some_and(|st| st.head_type != crate::model::style::HeadType::None);
        let broken = para.line_segs.iter().enumerate().any(|(i, seg)| {{
            (seg.tag & LineSeg::TAG_PARAGRAPH_HEAD != 0) != (head && i == 0)
        }});
        if broken {{
            claude_set_line_head_flags(para, styles);
        }}
        for ctrl in para.controls.iter_mut() {{
            if let Control::Table(t) = ctrl {{
                for cell in t.cells.iter_mut() {{
                    claude_repair_line_head_flags(&mut cell.paragraphs, styles);
                }}
            }}
        }}
    }}
}}

{SIG}    let preserved = reflow_line_segs_inner(para, paragraph_box, styles, dpi, preserve_prefix_for_edit, split_stale_cell_reflow);
    claude_set_line_head_flags(para, styles);
    preserved
}}

fn reflow_line_segs_inner(
    para: &mut Paragraph,
    paragraph_box: ParagraphBox,
    styles: &ResolvedStyleSet,
    dpi: f64,
    preserve_prefix_for_edit: Option<usize>,
    split_stale_cell_reflow: bool,
) -> bool {{
"""

STY = "        let styles = resolve_styles_for_document(&document, DEFAULT_DPI);\n\n        let hwp5_origin_hwpx = matches!(source_format, crate::parser::FileFormat::Hwpx)\n"
STY_NEW = (
    "        let styles = resolve_styles_for_document(&document, DEFAULT_DPI);\n"
    f"        // {TAG}\n"
    "        if matches!(source_format, crate::parser::FileFormat::Hwpx) {\n"
    "            for sec in document.sections.iter_mut() {\n"
    "                crate::renderer::composer::claude_repair_line_head_flags(&mut sec.paragraphs, &styles);\n"
    "            }\n"
    "        }\n"
    "\n"
    "        let hwp5_origin_hwpx = matches!(source_format, crate::parser::FileFormat::Hwpx)\n"
)
EXP = "pub(crate) use line_breaking::claude_bullet_head_hwp;\n"

EDITS = [
    (LB, SIG, NEW),
    (
        "renderer/composer.rs",
        EXP,
        f"// {TAG}\npub(crate) use line_breaking::claude_repair_line_head_flags;\n"
        + EXP,
    ),
    ("document_core/commands/document.rs", STY, STY_NEW),
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
