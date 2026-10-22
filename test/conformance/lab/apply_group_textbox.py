"""개발용: 묶음 개체 안에 든 글상자도 편집할 수 있게 한다.

    python apply_group_textbox.py [--revert]

사용자 보고(2026-10-22, 서울형_탐구_수업-워크시트(한글).hwp): 1쪽 「탐구 단원 설계 / 워크시트」, 2쪽 「단원 설계의 중점」 아래 「가」 목록을
편집할 수 없다. 둘 다 묶음(그림 + 사각형, 또는 사각형 둘) 안 사각형의 글상자다. 엔진은 묶음 자식 글상자 글자를 묶음과 같은 개체 번호,
칸 번호 0 으로 그려, 커서를 넣으면 개체(묶음 자체)에서 글상자를 찾다 실패했다.
고침: 그릴 때 묶음 자식 글상자는 경로의 칸 번호에 자식 번호 경로(깊이마다 1024진수, 깊이 1 이면 자식 번호)를 싣고, 엔진이 글상자를 찾을 때
개체가 묶음이면 그 경로 끝 자식에서 찾는다(글상자는 원래 칸 번호가 0 이어야 했으므로 다른 개체의 동작은 같다). 「단원 설계의 중점」은
바깥 묶음 안 묶음의 자식이다.
글상자 폭은 그리기와 같이 원래 폭 x 묶음 배율.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx group-textbox]"
TE = "document_core/commands/text_editing.rs"

EDITS = [
    (
        "document_core/helpers.rs",
        "/// ShapeObject에서 캡션을 추출하는 헬퍼 (#4321).\n",
        f"/// {TAG} 묶음 자식 경로를 글상자 칸 번호 하나에 싣는다(깊이마다 1024진수, 자식 번호 + 1). 깊이 1 이면 자식 번호 그대로.\n"
        "pub(crate) fn claude_group_path_encode(path: &[usize]) -> usize {\n"
        "    let mut code = 0usize;\n"
        "    for (k, &i) in path.iter().enumerate() {\n"
        "        code += (i + 1) << (10 * k);\n"
        "    }\n"
        "    code.saturating_sub(1)\n"
        "}\n"
        "\n"
        f"/// {TAG} `claude_group_path_encode` 를 되돌린다\n"
        "pub(crate) fn claude_group_path_decode(code: usize) -> Vec<usize> {\n"
        "    let mut c = code + 1;\n"
        "    let mut out = Vec::new();\n"
        "    while c > 0 {\n"
        "        out.push((c & 1023).saturating_sub(1));\n"
        "        c >>= 10;\n"
        "    }\n"
        "    out\n"
        "}\n"
        "\n"
        f"/// {TAG} 묶음 경로 끝의 자식 도형\n"
        "fn claude_group_leaf(shape: &crate::model::shape::ShapeObject, idx: usize) -> Option<&crate::model::shape::ShapeObject> {\n"
        "    let mut node = shape;\n"
        "    for i in claude_group_path_decode(idx) {\n"
        "        match node {\n"
        "            crate::model::shape::ShapeObject::Group(g) => node = g.children.get(i)?,\n"
        "            _ => return None,\n"
        "        }\n"
        "    }\n"
        "    Some(node)\n"
        "}\n"
        "\n"
        f"/// {TAG} 개체와 칸 번호로 글상자를 찾는다. 묶음이면 칸 번호에 실은 자식 경로 끝 도형의 글상자, 아니면 칸 번호 0 일 때만 자기 글상자.\n"
        "pub(crate) fn claude_textbox_at(\n"
        "    shape: &crate::model::shape::ShapeObject,\n"
        "    idx: usize,\n"
        ") -> Option<&crate::model::shape::TextBox> {\n"
        "    match shape {\n"
        "        crate::model::shape::ShapeObject::Group(_) => claude_group_leaf(shape, idx).and_then(get_textbox_from_shape),\n"
        "        _ if idx == 0 => get_textbox_from_shape(shape),\n"
        "        _ => None,\n"
        "    }\n"
        "}\n"
        "\n"
        f"/// {TAG} `claude_textbox_at` 의 가변 판\n"
        "pub(crate) fn claude_textbox_at_mut(\n"
        "    shape: &mut crate::model::shape::ShapeObject,\n"
        "    idx: usize,\n"
        ") -> Option<&mut crate::model::shape::TextBox> {\n"
        "    if !matches!(shape, crate::model::shape::ShapeObject::Group(_)) {\n"
        "        return if idx == 0 { get_textbox_from_shape_mut(shape) } else { None };\n"
        "    }\n"
        "    let mut node = shape;\n"
        "    for i in claude_group_path_decode(idx) {\n"
        "        match node {\n"
        "            crate::model::shape::ShapeObject::Group(g) => node = g.children.get_mut(i)?,\n"
        "            _ => return None,\n"
        "        }\n"
        "    }\n"
        "    get_textbox_from_shape_mut(node)\n"
        "}\n"
        "\n"
        f"/// {TAG} 글상자 바깥 폭(HWPUNIT). 묶음 자식은 자기 common 크기가 0 이라 그리기와 같이 원래 폭 x 합성 배율로 잰다.\n"
        "pub(crate) fn claude_textbox_owner_width(shape: &crate::model::shape::ShapeObject, idx: usize) -> i32 {\n"
        "    match shape {\n"
        "        crate::model::shape::ShapeObject::Group(_) => claude_group_leaf(shape, idx)\n"
        "            .map(|c| {\n"
        "                let sa = c.shape_attr();\n"
        "                let w = (sa.original_width as f64 * sa.render_sx).abs() as i32;\n"
        "                if w > 0 { w } else { sa.current_width as i32 }\n"
        "            })\n"
        "            .unwrap_or(0),\n"
        "        _ => shape.common().width as i32,\n"
        "    }\n"
        "}\n"
        "\n"
        "/// ShapeObject에서 캡션을 추출하는 헬퍼 (#4321).\n",
    ),
    (
        TE,
        "                if cell_idx != 0 {\n"
        "                    return Err(HwpError::RenderError(format!(\n"
        '                        "글상자 셀 인덱스는 0이어야 합니다 (요청: {})",\n'
        "                        cell_idx\n"
        "                    )));\n"
        "                }\n"
        "                let tb =\n"
        "                    super::super::helpers::get_textbox_from_shape_mut(shape).ok_or_else(|| {\n",
        f"                // {TAG} 묶음이면 cell_idx 번째 자식의 글상자(다른 도형은 cell_idx 0 만)\n"
        "                let tb =\n"
        "                    super::super::helpers::claude_textbox_at_mut(shape, cell_idx).ok_or_else(|| {\n",
    ),
    (
        TE,
        "                if let Some(tb) = super::super::helpers::get_textbox_from_shape_mut(shape) {\n"
        "                    if let Some(cell_para) = tb.paragraphs.get_mut(cell_para_idx) {\n",
        "                if let Some(tb) = super::super::helpers::claude_textbox_at_mut(shape, cell_idx) {\n"
        "                    if let Some(cell_para) = tb.paragraphs.get_mut(cell_para_idx) {\n",
    ),
    (
        TE,
        "                let Some(textbox) = super::super::helpers::get_textbox_from_shape_mut(shape) else {\n",
        "                let Some(textbox) = super::super::helpers::claude_textbox_at_mut(shape, cell_idx) else {\n",
    ),
    (
        TE,
        "                let tb = super::super::helpers::get_textbox_from_shape(shape)?;\n"
        "                let common = shape.common();\n"
        "                Some((common.width as i32, tb.margin_left, tb.margin_right))\n",
        "                let tb = super::super::helpers::claude_textbox_at(shape, cell_idx)?;\n"
        "                let width = super::super::helpers::claude_textbox_owner_width(shape, cell_idx);\n"
        "                Some((width, tb.margin_left, tb.margin_right))\n",
    ),
    (
        TE,
        "                Control::Shape(s) => super::super::helpers::get_textbox_from_shape(s)?\n"
        "                    .paragraphs\n"
        "                    .get(cell_para_idx)?,\n",
        "                Control::Shape(s) => super::super::helpers::claude_textbox_at(s, cell_idx)?\n"
        "                    .paragraphs\n"
        "                    .get(cell_para_idx)?,\n",
    ),
    (
        TE,
        "                if cell_idx != 0 {\n"
        "                    return None;\n"
        "                }\n"
        "                get_textbox_from_shape(shape)?.paragraphs.get(cell_para_idx)\n",
        "                super::super::helpers::claude_textbox_at(shape, cell_idx)?.paragraphs.get(cell_para_idx)\n",
    ),
    (
        TE,
        "                if let Some(tb) = super::super::helpers::get_textbox_from_shape_mut(shape) {\n"
        "                    tb.paragraphs.insert(new_cell_para_idx, new_para);\n",
        "                if let Some(tb) = super::super::helpers::claude_textbox_at_mut(shape, cell_idx) {\n"
        "                    tb.paragraphs.insert(new_cell_para_idx, new_para);\n",
    ),
    (
        TE,
        "                if let Some(tb) = super::super::helpers::get_textbox_from_shape_mut(shape) {\n"
        "                    let removed = tb.paragraphs.remove(cell_para_idx);\n",
        "                if let Some(tb) = super::super::helpers::claude_textbox_at_mut(shape, cell_idx) {\n"
        "                    let removed = tb.paragraphs.remove(cell_para_idx);\n",
    ),
    (
        TE,
        "                let text_box = get_textbox_from_shape(shape)\n"
        '                    .ok_or_else(|| HwpError::RenderError("도형에 글상자가 없습니다".to_string()))?;\n'
        "                Ok(text_box.paragraphs.len())\n",
        "                let text_box = super::super::helpers::claude_textbox_at(shape, cell_idx)\n"
        '                    .ok_or_else(|| HwpError::RenderError("도형에 글상자가 없습니다".to_string()))?;\n'
        "                Ok(text_box.paragraphs.len())\n",
    ),
    (
        TE,
        "                    if cell_idx != 0 {\n"
        "                        return Err(HwpError::RenderError(format!(\n"
        '                            "경로[{}]: 글상자의 cell_index는 0이어야 합니다 ({})",\n'
        "                            i, cell_idx\n"
        "                        )));\n"
        "                    }\n"
        "                    let text_box = super::super::helpers::get_textbox_from_shape_mut(shape)\n",
        "                    let text_box = super::super::helpers::claude_textbox_at_mut(shape, cell_idx)\n",
    ),
    (
        "document_core/commands/clipboard.rs",
        "                Control::Shape(s) => {\n"
        "                    &mut super::super::helpers::get_textbox_from_shape_mut(s)\n"
        '                        .ok_or_else(|| HwpError::RenderError("글상자 없음".to_string()))?\n',
        "                Control::Shape(s) => {\n"
        f"                    // {TAG} 묶음이면 칸 번호에 실은 자식 경로의 글상자\n"
        "                    &mut super::super::helpers::claude_textbox_at_mut(s, cell_idx)\n"
        '                        .ok_or_else(|| HwpError::RenderError("글상자 없음".to_string()))?\n',
    ),
    # 그리기: 묶음 자식 글상자는 경로 칸 번호에 자식 번호 경로
    (
        "renderer/layout/shape_layout.rs",
        "                for (_ci, child) in group.children.iter().enumerate() {\n"
        "                    let sa = child.shape_attr();\n",
        "                for (_ci, child) in group.children.iter().enumerate() {\n"
        f"                    // {TAG} 묶음 자식의 글상자 글자는 칸 번호 자리에 자식 번호 경로를 싣는다(묶음 안 묶음 포함)\n"
        "                    CLAUDE_GROUP_PATH.with(|p| {\n"
        "                        let mut p = p.borrow_mut();\n"
        "                        if _ci == 0 {\n"
        "                            p.push(0);\n"
        "                        }\n"
        "                        if let Some(last) = p.last_mut() {\n"
        "                            *last = _ci;\n"
        "                        }\n"
        "                    });\n"
        "                    let sa = child.shape_attr();\n",
    ),
    (
        "renderer/layout/shape_layout.rs",
        "                parent.children.push(group_node);\n            }\n            ShapeObject::Picture(pic) => {\n",
        f"                // {TAG} 묶음을 다 그렸으면 경로에서 이 묶음 자리를 뺀다\n"
        "                if !group.children.is_empty() {\n"
        "                    CLAUDE_GROUP_PATH.with(|p| {\n"
        "                        p.borrow_mut().pop();\n"
        "                    });\n"
        "                }\n"
        "                parent.children.push(group_node);\n            }\n            ShapeObject::Picture(pic) => {\n",
    ),
    (
        "renderer/layout/shape_layout.rs",
        "fn textbox_vpos_origin_hu(common: &CommonObjAttr, matrix_positioned: bool) -> Option<i32> {\n",
        "thread_local! {\n"
        f"    /// {TAG} 지금 그리는 묶음 자식 번호 경로(바깥 묶음부터, 글상자 경로 칸 번호로 싣는다)\n"
        "    pub(crate) static CLAUDE_GROUP_PATH: std::cell::RefCell<Vec<usize>> = const { std::cell::RefCell::new(Vec::new()) };\n"
        "}\n"
        "\n"
        f"/// {TAG} 글상자 셀 경로의 칸 번호: 묶음 자식이면 자식 번호 경로, 아니면 0\n"
        "fn claude_group_cell_index() -> usize {\n"
        "    CLAUDE_GROUP_PATH.with(|g| {\n"
        "        let g = g.borrow();\n"
        "        if g.is_empty() { 0 } else { crate::document_core::helpers::claude_group_path_encode(&g) }\n"
        "    })\n"
        "}\n"
        "\n"
        "fn textbox_vpos_origin_hu(common: &CommonObjAttr, matrix_positioned: bool) -> Option<i32> {\n",
    ),
] + [
    # 글상자 안 문맥을 만드는 다섯 자리(가로 문단 둘, 그림, 수식, 세로 글상자)의 칸 번호
    (
        "renderer/layout/shape_layout.rs",
        f"{lead}control_index,\n{lead}cell_index: 0,\n{lead}cell_para_index: {cpi},\n",
        f"{lead}control_index,\n{lead}cell_index: claude_group_cell_index(), // {TAG}\n{lead}cell_para_index: {cpi},\n",
    )
    for lead, cpi in [
        (" " * 32, "tb_para_idx"),
        (" " * 24, "tb_para_idx"),
        (" " * 28, "ci.cell_para_index"),
    ]
]
# 그림, 수식 두 자리는 같은 꼴이라 앞 줄로 가른다
EDITS += [
    (
        "document_core/queries/cursor_rect.rs",
        "                if outer.cell_index == 0 {\n"
        "                    let is_shape = self\n"
        "                        .document\n"
        "                        .sections\n"
        "                        .get(run.section_index)\n"
        "                        .and_then(|s| s.paragraphs.get(ctx.parent_para_index))\n"
        "                        .and_then(|p| p.controls.get(outer.control_index))\n"
        "                        .map(|c| matches!(c, Control::Shape(_)))\n"
        "                        .unwrap_or(false);\n"
        "                    run.is_textbox = is_shape;\n"
        "                } else {\n"
        "                    run.is_textbox = false;\n"
        "                }\n",
        f"                // {TAG} 도형이면 칸 번호(묶음 자식 경로)와 상관없이 글상자다(표 칸은 개체가 표라 false)\n"
        "                run.is_textbox = self\n"
        "                    .document\n"
        "                    .sections\n"
        "                    .get(run.section_index)\n"
        "                    .and_then(|s| s.paragraphs.get(ctx.parent_para_index))\n"
        "                    .and_then(|p| p.controls.get(outer.control_index))\n"
        "                    .map(|c| matches!(c, Control::Shape(_)))\n"
        "                    .unwrap_or(false);\n",
    ),
    (
        "document_core/queries/cursor_nav.rs",
        "            let is_tb = cei == 0\n                && self\n",
        f"            // {TAG} 도형이면 칸 번호(묶음 자식 경로)와 상관없이 글상자\n"
        "            let is_tb = self\n",
    ),
    (
        "document_core/queries/rendering.rs",
        "                let valid = super::super::helpers::get_textbox_from_shape(shape)\n"
        "                    .is_some_and(|textbox| cell_para_idx < textbox.paragraphs.len());\n",
        f"                // {TAG} 묶음 자식 글상자(칸 번호에 자식 경로)도 검증한다\n"
        "                let valid = super::super::helpers::claude_textbox_at(shape, cell_idx)\n"
        "                    .is_some_and(|textbox| cell_para_idx < textbox.paragraphs.len());\n",
    ),
    (
        "renderer/layout/shape_layout.rs",
        "                        let pic_cell_ctx = CellContext {\n"
        "                            in_textbox: true,\n"
        "                            parent_para_index: para_index,\n"
        "                            path: {\n"
        "                                let mut p = parent_cell_path.to_vec();\n"
        "                                p.push(CellPathEntry {\n"
        "                                    control_index,\n"
        "                                    cell_index: 0,\n",
        "                        let pic_cell_ctx = CellContext {\n"
        "                            in_textbox: true,\n"
        "                            parent_para_index: para_index,\n"
        "                            path: {\n"
        "                                let mut p = parent_cell_path.to_vec();\n"
        "                                p.push(CellPathEntry {\n"
        "                                    control_index,\n"
        f"                                    cell_index: claude_group_cell_index(), // {TAG}\n",
    ),
    (
        "renderer/layout/shape_layout.rs",
        "                        let equiv_cell_ctx = CellContext {\n"
        "                            in_textbox: true,\n"
        "                            parent_para_index: para_index,\n"
        "                            path: {\n"
        "                                let mut p = parent_cell_path.to_vec();\n"
        "                                p.push(CellPathEntry {\n"
        "                                    control_index,\n"
        "                                    cell_index: 0,\n",
        "                        let equiv_cell_ctx = CellContext {\n"
        "                            in_textbox: true,\n"
        "                            parent_para_index: para_index,\n"
        "                            path: {\n"
        "                                let mut p = parent_cell_path.to_vec();\n"
        "                                p.push(CellPathEntry {\n"
        "                                    control_index,\n"
        f"                                    cell_index: claude_group_cell_index(), // {TAG}\n",
    ),
]


def main():
    revert = "--revert" in sys.argv
    for rel, find, repl in EDITS:
        if find == repl:
            continue
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
