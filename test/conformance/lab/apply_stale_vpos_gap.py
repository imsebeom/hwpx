"""개발용: 저장 세로 위치가 앞 문단 끝보다 뒤로 벌어진 낡은 값을 열 때 닫는다.

    python apply_stale_vpos_gap.py [--revert]

근거(2026-10-31, 문항 _19 자료 1 아래 여백): 칸과 본문의 뒤 문단 vertpos 를 사본에서 ±밀어도 한/글 PDF 는 그대로이고 엔진만 움직였다(실험 5종).
떠 있는 개체가 없는 이웃 문단에서 뒤 문단이 「앞 끝 줄 위치 + 높이 + 간격 + 문단 아래위 간격」보다 큰 경우는 새 조판 정답본 30,400쌍 중 3건, _19 는 20건.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx stale-vpos-gap]"
LB = "renderer/composer/line_breaking.rs"

A1 = f"/// {'[claude-hwpx line-head-flags]'} 열 때: 글머리 비트가 규칙과 어긋난 문단만 고친다."
FN = f"""/// {TAG} 열 때: 떠 있는 개체가 없는 이웃 문단 사이가 앞 문단 끝보다 벌어져 있으면 낡은 값으로 보고 뒤 문단들을 당긴다.
/// 쪽이나 단이 바뀌어 위치가 되돌아가는 문단에서 당기기를 멈춘다. 한/글은 저장 세로 위치를 쓰지 않고 다시 쌓는다.
pub(crate) fn claude_close_stale_vpos_gaps(paras: &mut [Paragraph], shapes: &[crate::model::style::ParaShape]) {{
    fn floats(p: &Paragraph) -> bool {{
        p.controls.iter().any(|c| match c {{
            Control::Table(t) => !t.common.treat_as_char,
            Control::Picture(x) => !x.common.treat_as_char,
            Control::Shape(s) => !s.common().treat_as_char,
            _ => false,
        }})
    }}
    let spacing = |p: &Paragraph| {{
        shapes
            .get(p.para_shape_id as usize)
            .map(|s| (s.spacing_before, s.spacing_after))
            .unwrap_or((0, 0))
    }};
    let mut shift = 0i32;
    let mut prev: Option<(i32, i32, bool)> = None; // 저장 끝 위치, 아래 간격, 떠 있는 개체
    for para in paras.iter_mut() {{
        let is_float = floats(para);
        let Some(first) = para.line_segs.first() else {{
            prev = None;
            shift = 0;
            continue;
        }};
        let raw = first.vertical_pos;
        let new_area = raw == 0 || first.tag & (LineSeg::TAG_FIRST_LINE_OF_PAGE | LineSeg::TAG_FIRST_LINE_OF_COLUMN) != 0;
        let (before, after) = spacing(para);
        if new_area {{
            shift = 0;
        }} else if let Some((end, prev_after, prev_float)) = prev {{
            let gap = raw - (end + prev_after + before);
            if gap < -2 {{
                shift = 0;
            }} else if gap > 2 && !is_float && !prev_float {{
                shift += gap;
            }}
        }}
        let last = para.line_segs.last().unwrap();
        prev = Some((last.vertical_pos + last.line_height + last.line_spacing, after, is_float));
        if shift != 0 {{
            for seg in para.line_segs.iter_mut() {{
                seg.vertical_pos -= shift;
            }}
        }}
    }}
    for para in paras.iter_mut() {{
        for ctrl in para.controls.iter_mut() {{
            if let Control::Table(t) = ctrl {{
                for cell in t.cells.iter_mut() {{
                    claude_close_stale_vpos_gaps(&mut cell.paragraphs, shapes);
                }}
            }}
        }}
    }}
}}

"""
D = (
    "            for sec in document.sections.iter_mut() {\n"
    "                crate::renderer::composer::claude_repair_line_head_flags(&mut sec.paragraphs, &styles);\n"
    "            }\n"
)
D2 = (
    "            let para_shapes = document.doc_info.para_shapes.clone();\n"
    "            for sec in document.sections.iter_mut() {\n"
    "                crate::renderer::composer::claude_repair_line_head_flags(&mut sec.paragraphs, &styles);\n"
    f"                // {TAG}\n"
    "                crate::renderer::composer::claude_close_stale_vpos_gaps(&mut sec.paragraphs, &para_shapes);\n"
    "            }\n"
)
E1 = "pub(crate) use line_breaking::claude_repair_line_head_flags;\n"

EDITS = [
    (LB, A1, FN + A1),
    (
        "renderer/composer.rs",
        E1,
        E1 + f"// {TAG}\npub(crate) use line_breaking::claude_close_stale_vpos_gaps;\n",
    ),
    ("document_core/commands/document.rs", D, D2),
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
