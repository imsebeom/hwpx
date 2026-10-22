// ==== find ====
fn textbox_vpos_origin_hu(common: &CommonObjAttr, matrix_positioned: bool) -> Option<i32> {
// ==== replace ====
/// [claude-hwpx transparent-shape] 투명선 보기: 선 없는 도형의 테두리를 표 투명선과 같은 빨간 점선으로 그린다
fn claude_transparent_outline(
    tree: &mut PageLayoutContext,
    node: &mut RenderNode,
    bbox: BoundingBox,
    transform: ShapeTransform,
) {
    let style = ShapeStyle {
        stroke_color: Some(0x0000FF),
        stroke_width: 0.4,
        stroke_dash: super::super::StrokeDash::Dot,
        ..ShapeStyle::default()
    };
    let mut rect = RectangleNode::new(0.0, style, None);
    rect.transform = transform;
    let id = tree.next_id();
    node.children.push(RenderNode::new(id, RenderNodeType::Rectangle(rect), bbox));
}

fn textbox_vpos_origin_hu(common: &CommonObjAttr, matrix_positioned: bool) -> Option<i32> {
// ==== next ====
                let round_px = if rect.round_rate > 0 {
                    (rect.round_rate as f64 / 100.0) * render_w.min(render_h) / 2.0
                } else {
                    0.0
                };
                let node_id = tree.next_id();
// ==== replace ====
                let round_px = if rect.round_rate > 0 {
                    (rect.round_rate as f64 / 100.0) * render_w.min(render_h) / 2.0
                } else {
                    0.0
                };
                // [claude-hwpx transparent-shape]
                let claude_no_line = style.stroke_color.is_none() || style.stroke_width <= 0.0;
                let node_id = tree.next_id();
// ==== next ====
                    BoundingBox::new(render_x, render_y, render_w, render_h),
                );
                // 이미지 채우기가 있으면 자식으로 이미지 노드 추가
// ==== replace ====
                    BoundingBox::new(render_x, render_y, render_w, render_h),
                );
                // [claude-hwpx transparent-shape] 투명선 보기면 선 없는 사각형에 점선 테두리
                if claude_no_line && self.show_transparent_borders.get() {
                    claude_transparent_outline(
                        tree,
                        &mut node,
                        BoundingBox::new(render_x, render_y, render_w, render_h),
                        transform,
                    );
                }
                // 이미지 채우기가 있으면 자식으로 이미지 노드 추가
// ==== next ====
                let (style, gradient) = drawing_to_shape_style(&ellipse.drawing);
                let node_id = tree.next_id();
                let mut ell_node = EllipseNode::new(style, gradient);
// ==== replace ====
                let (style, gradient) = drawing_to_shape_style(&ellipse.drawing);
                // [claude-hwpx transparent-shape]
                let claude_no_line = style.stroke_color.is_none() || style.stroke_width <= 0.0;
                let node_id = tree.next_id();
                let mut ell_node = EllipseNode::new(style, gradient);
// ==== next ====
                    RenderNodeType::Ellipse(ell_node),
                    BoundingBox::new(render_x, render_y, render_w, render_h),
                );
// ==== replace ====
                    RenderNodeType::Ellipse(ell_node),
                    BoundingBox::new(render_x, render_y, render_w, render_h),
                );
                // [claude-hwpx transparent-shape] 투명선 보기면 선 없는 타원의 외곽 상자를 점선으로
                if claude_no_line && self.show_transparent_borders.get() {
                    claude_transparent_outline(
                        tree,
                        &mut node,
                        BoundingBox::new(render_x, render_y, render_w, render_h),
                        transform,
                    );
                }
