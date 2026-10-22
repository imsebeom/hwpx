"""개발용: 보기 → 투명선을 켜면 선 없는 사각형(글상자)과 타원의 테두리를 표의 투명선처럼 빨간 점선으로 그린다.

    python apply_transparent_shape.py [--revert]

사용자 지시(2026-10-23, 워크시트 hwp): 「보기 → 투명선을 켜도 선 없는 개체의 테두리가 안 보임 -> 보이게 하라」.
엔진의 투명선은 표 칸 테두리(border_rendering.rs render_transparent_borders, 빨간 0.4px 점선)에만 있었다.
선 종류 「없음」이거나 묶음 자식 글상자의 보조선을 지운 사각형, 선 없는 타원에 같은 모양의 점선 사각형을 자식으로 붙인다.
화면 보기 설정이라 인쇄와 내보내기(투명선 끔)에는 영향이 없다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx transparent-shape]"
F = "renderer/layout/shape_layout.rs"

EDITS = [
    (
        F,
        "fn textbox_vpos_origin_hu(common: &CommonObjAttr, matrix_positioned: bool) -> Option<i32> {\n",
        f"/// {TAG} 투명선 보기: 선 없는 도형의 테두리를 표 투명선과 같은 빨간 점선으로 그린다\n"
        "fn claude_transparent_outline(\n"
        "    tree: &mut PageLayoutContext,\n"
        "    node: &mut RenderNode,\n"
        "    bbox: BoundingBox,\n"
        "    transform: ShapeTransform,\n"
        ") {\n"
        "    let style = ShapeStyle {\n"
        "        stroke_color: Some(0x0000FF),\n"
        "        stroke_width: 0.4,\n"
        "        stroke_dash: super::super::StrokeDash::Dot,\n"
        "        ..ShapeStyle::default()\n"
        "    };\n"
        "    let mut rect = RectangleNode::new(0.0, style, None);\n"
        "    rect.transform = transform;\n"
        "    let id = tree.next_id();\n"
        "    node.children.push(RenderNode::new(id, RenderNodeType::Rectangle(rect), bbox));\n"
        "}\n"
        "\n"
        "fn textbox_vpos_origin_hu(common: &CommonObjAttr, matrix_positioned: bool) -> Option<i32> {\n",
    ),
    (
        F,
        "                let round_px = if rect.round_rate > 0 {\n"
        "                    (rect.round_rate as f64 / 100.0) * render_w.min(render_h) / 2.0\n"
        "                } else {\n"
        "                    0.0\n"
        "                };\n"
        "                let node_id = tree.next_id();\n",
        "                let round_px = if rect.round_rate > 0 {\n"
        "                    (rect.round_rate as f64 / 100.0) * render_w.min(render_h) / 2.0\n"
        "                } else {\n"
        "                    0.0\n"
        "                };\n"
        f"                // {TAG}\n"
        "                let claude_no_line = style.stroke_color.is_none() || style.stroke_width <= 0.0;\n"
        "                let node_id = tree.next_id();\n",
    ),
    (
        F,
        "                    BoundingBox::new(render_x, render_y, render_w, render_h),\n"
        "                );\n"
        "                // 이미지 채우기가 있으면 자식으로 이미지 노드 추가\n",
        "                    BoundingBox::new(render_x, render_y, render_w, render_h),\n"
        "                );\n"
        f"                // {TAG} 투명선 보기면 선 없는 사각형에 점선 테두리\n"
        "                if claude_no_line && self.show_transparent_borders.get() {\n"
        "                    claude_transparent_outline(\n"
        "                        tree,\n"
        "                        &mut node,\n"
        "                        BoundingBox::new(render_x, render_y, render_w, render_h),\n"
        "                        transform,\n"
        "                    );\n"
        "                }\n"
        "                // 이미지 채우기가 있으면 자식으로 이미지 노드 추가\n",
    ),
    (
        F,
        "                let (style, gradient) = drawing_to_shape_style(&ellipse.drawing);\n"
        "                let node_id = tree.next_id();\n"
        "                let mut ell_node = EllipseNode::new(style, gradient);\n",
        "                let (style, gradient) = drawing_to_shape_style(&ellipse.drawing);\n"
        f"                // {TAG}\n"
        "                let claude_no_line = style.stroke_color.is_none() || style.stroke_width <= 0.0;\n"
        "                let node_id = tree.next_id();\n"
        "                let mut ell_node = EllipseNode::new(style, gradient);\n",
    ),
    (
        F,
        "                    RenderNodeType::Ellipse(ell_node),\n"
        "                    BoundingBox::new(render_x, render_y, render_w, render_h),\n"
        "                );\n",
        "                    RenderNodeType::Ellipse(ell_node),\n"
        "                    BoundingBox::new(render_x, render_y, render_w, render_h),\n"
        "                );\n"
        f"                // {TAG} 투명선 보기면 선 없는 타원의 외곽 상자를 점선으로\n"
        "                if claude_no_line && self.show_transparent_borders.get() {\n"
        "                    claude_transparent_outline(\n"
        "                        tree,\n"
        "                        &mut node,\n"
        "                        BoundingBox::new(render_x, render_y, render_w, render_h),\n"
        "                        transform,\n"
        "                    );\n"
        "                }\n",
    ),
]


def main():
    revert = "--revert" in sys.argv
    for rel, find, repl in EDITS:
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
