// ==== find ====
/// ShapeObject에서 캡션을 추출하는 헬퍼 (#4321).
// ==== replace ====
/// [claude-hwpx group-textbox] 묶음 자식 경로를 글상자 칸 번호 하나에 싣는다(깊이마다 1024진수, 자식 번호 + 1). 깊이 1 이면 자식 번호 그대로.
pub(crate) fn claude_group_path_encode(path: &[usize]) -> usize {
    let mut code = 0usize;
    for (k, &i) in path.iter().enumerate() {
        code += (i + 1) << (10 * k);
    }
    code.saturating_sub(1)
}

/// [claude-hwpx group-textbox] `claude_group_path_encode` 를 되돌린다
pub(crate) fn claude_group_path_decode(code: usize) -> Vec<usize> {
    let mut c = code + 1;
    let mut out = Vec::new();
    while c > 0 {
        out.push((c & 1023).saturating_sub(1));
        c >>= 10;
    }
    out
}

/// [claude-hwpx group-textbox] 묶음 경로 끝의 자식 도형
fn claude_group_leaf(shape: &crate::model::shape::ShapeObject, idx: usize) -> Option<&crate::model::shape::ShapeObject> {
    let mut node = shape;
    for i in claude_group_path_decode(idx) {
        match node {
            crate::model::shape::ShapeObject::Group(g) => node = g.children.get(i)?,
            _ => return None,
        }
    }
    Some(node)
}

/// [claude-hwpx group-textbox] 개체와 칸 번호로 글상자를 찾는다. 묶음이면 칸 번호에 실은 자식 경로 끝 도형의 글상자, 아니면 칸 번호 0 일 때만 자기 글상자.
pub(crate) fn claude_textbox_at(
    shape: &crate::model::shape::ShapeObject,
    idx: usize,
) -> Option<&crate::model::shape::TextBox> {
    match shape {
        crate::model::shape::ShapeObject::Group(_) => claude_group_leaf(shape, idx).and_then(get_textbox_from_shape),
        _ if idx == 0 => get_textbox_from_shape(shape),
        _ => None,
    }
}

/// [claude-hwpx group-textbox] `claude_textbox_at` 의 가변 판
pub(crate) fn claude_textbox_at_mut(
    shape: &mut crate::model::shape::ShapeObject,
    idx: usize,
) -> Option<&mut crate::model::shape::TextBox> {
    if !matches!(shape, crate::model::shape::ShapeObject::Group(_)) {
        return if idx == 0 { get_textbox_from_shape_mut(shape) } else { None };
    }
    let mut node = shape;
    for i in claude_group_path_decode(idx) {
        match node {
            crate::model::shape::ShapeObject::Group(g) => node = g.children.get_mut(i)?,
            _ => return None,
        }
    }
    get_textbox_from_shape_mut(node)
}

/// [claude-hwpx group-textbox] 글상자 바깥 폭(HWPUNIT). 묶음 자식은 자기 common 크기가 0 이라 그리기와 같이 원래 폭 x 합성 배율로 잰다.
pub(crate) fn claude_textbox_owner_width(shape: &crate::model::shape::ShapeObject, idx: usize) -> i32 {
    match shape {
        crate::model::shape::ShapeObject::Group(_) => claude_group_leaf(shape, idx)
            .map(|c| {
                let sa = c.shape_attr();
                let w = (sa.original_width as f64 * sa.render_sx).abs() as i32;
                if w > 0 { w } else { sa.current_width as i32 }
            })
            .unwrap_or(0),
        _ => shape.common().width as i32,
    }
}

/// ShapeObject에서 캡션을 추출하는 헬퍼 (#4321).
