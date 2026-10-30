"""개발용: 표 속 표 칸의 글자처럼 취급 그림 옆 캐럿과 클릭 판정. cell-inline-caret, cell-pic-hit 은 칸 경로가 한 겹일 때만 돌았다.

    python apply_nested_pic_caret.py [--revert]

근거(2026-10-30 사용자 보고, 문항3삭제판 11쪽 자료 2 그래프): 그림 오른쪽을 눌러도 캐럿이 왼쪽에 서고, End 로 간 오른쪽 캐럿은
그림 아래쪽(높이 12)에, Home 은 다른 줄에 그려졌다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx nested-pic-caret]"
REL = "document_core/queries/cursor_rect.rs"


def hit_call(var, ref):
    return (
        f"if let Some(ctx) = {var}[idx].cell_context.as_ref().filter(|c| c.path.len() > 1) {{\n"
        "                        let p: Vec<(usize, usize, usize)> =\n"
        "                            ctx.path.iter().map(|e| (e.control_index, e.cell_index, e.cell_para_index)).collect();\n"
        f"                        if let Some((off, cx)) = self.claude_nested_pic_hit({var}[idx].section_index, ctx.parent_para_index, &p, x) {{\n"
        f"                            return Ok(Self::claude_hit_with_x(format_hit({ref}[idx], off, page_num), cx));\n"
        "                        }\n"
        "                    }\n"
        "                    "
    )


FNS = f"""    /// {TAG} 표 속 표 칸 문단의 글자처럼 취급 그림 옆 캐럿 (쪽, x, y, 높이). 그림 앞이면 왼쪽 끝, 뒤면 오른쪽 끝.
    pub(crate) fn claude_nested_pic_caret(
        &self,
        section_idx: usize,
        parent_para_idx: usize,
        path: &[(usize, usize, usize)],
        offset: usize,
    ) -> Option<(u32, f64, f64, f64)> {{
        use crate::renderer::render_tree::{{RenderNode, RenderNodeType}};
        let para = self.resolve_paragraph_by_path(section_idx, parent_para_idx, path).ok()?;
        let positions = find_logical_control_positions(para);
        let tac: Vec<usize> = para
            .controls
            .iter()
            .enumerate()
            .filter(|(_, c)| matches!(c, Control::Picture(p) if p.common.treat_as_char))
            .map(|(i, _)| i)
            .collect();
        let (k, after) = tac
            .iter()
            .find(|&&k| positions.get(k).map_or(false, |&p| p + 1 == offset))
            .map(|&k| (k, true))
            .or_else(|| tac.iter().find(|&&k| positions.get(k) == Some(&offset)).map(|&k| (k, false)))?;
        let Control::Picture(pic) = para.controls.get(k)? else {{
            return None;
        }};
        let bin = pic.image_attr.bin_data_id;
        fn find_img(node: &RenderNode, sec: usize, bin: u16) -> Option<(f64, f64, f64, f64)> {{
            if let RenderNodeType::Image(ref im) = node.node_type {{
                if im.section_index == Some(sec) && im.bin_data_id == bin {{
                    return Some((node.bbox.x, node.bbox.y, node.bbox.width, node.bbox.height));
                }}
            }}
            node.children.iter().find_map(|c| find_img(c, sec, bin))
        }}
        let (c0, c1, c2) = *path.first()?;
        let pages = self
            .find_pages_for_cell_position(section_idx, parent_para_idx, c0, c1, Some((c2, 0)))
            .ok()?;
        for &page_num in &pages {{
            let Ok(tree) = self.build_page_tree(page_num) else {{
                continue;
            }};
            if let Some((x, y, w, h)) = find_img(&tree.root, section_idx, bin) {{
                return Some((page_num, if after {{ x + w }} else {{ x }}, y, h));
            }}
        }}
        None
    }}

    /// {TAG} 글 없이 그림만 있는 표 속 표 칸 문단을 눌렀을 때 클릭 x 에 가장 가까운 자리와 캐럿 x.
    pub(crate) fn claude_nested_pic_hit(
        &self,
        section_idx: usize,
        parent_para_idx: usize,
        path: &[(usize, usize, usize)],
        x: f64,
    ) -> Option<(usize, f64)> {{
        let para = self.resolve_paragraph_by_path(section_idx, parent_para_idx, path).ok()?;
        if !para.text.trim().is_empty()
            || !para.controls.iter().any(|c| matches!(c, Control::Picture(p) if p.common.treat_as_char))
        {{
            return None;
        }}
        let slots = para.controls.iter().filter(|c| c.is_logical_inline()).count();
        let mut best: Option<(usize, f64)> = None;
        for off in 0..=slots {{
            let Some((_, cx, _, _)) = self.claude_nested_pic_caret(section_idx, parent_para_idx, path, off) else {{
                continue;
            }};
            if best.map_or(true, |(_, bx)| (cx - x).abs() < (bx - x).abs()) {{
                best = Some((off, cx));
            }}
        }}
        best
    }}

"""

ANCHOR = "    /// 페이지 좌표에서 문서 위치 찾기 (네이티브)\n"
A1 = (
    "if let Some(ctx) = runs[idx].cell_context.as_ref().filter(|c| c.path.len() == 1) {"
)
A2 = "if let Some(ctx) = line_runs[idx].cell_context.as_ref().filter(|c| c.path.len() == 1) {"
A3 = "        } else {\n            char_offset\n        };\n"

EDITS = [
    (REL, ANCHOR, FNS + ANCHOR),
    (REL, A1, hit_call("runs", "&runs") + A1),
    (REL, A2, hit_call("line_runs", "line_runs") + A2),
    (
        REL,
        A3,
        (
            "        } else {\n"
            "            if let Some((pg, x, y, h)) =\n"
            "                self.claude_nested_pic_caret(section_idx, parent_para_idx, &path, char_offset)\n"
            "            {\n"
            "                return Ok(format_cursor_rect_json(pg, x, y, h, None));\n"
            "            }\n"
            "            char_offset\n"
            "        };\n"
        ),
    ),
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
