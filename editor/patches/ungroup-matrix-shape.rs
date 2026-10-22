// ==== find ====
            // 자식의 로컬 좌표를 글로벌 좌표로 변환 (그룹 스케일 적용)
            {
                let c = child.common_mut();
                c.horizontal_offset =
                    (group_x + (c.horizontal_offset as f64 * group_sx) as i32) as u32;
                c.vertical_offset = (group_y + (c.vertical_offset as f64 * group_sy) as i32) as u32;
                c.width = ((c.width as f64 * group_sx).round().max(1.0)) as u32;
                c.height = ((c.height as f64 * group_sy).round().max(1.0)) as u32;
// ==== replace ====
            // [claude-hwpx ungroup-matrix] 그리기와 같은 합성 행렬(묶음 배율 포함)이 있고 회전이 없으면 그것으로 위치와 크기를 정한다
            let matrix = {
                let sa = child.shape_attr();
                if sa.render_sx.abs() > 1e-9
                    && sa.render_sy.abs() > 1e-9
                    && sa.render_b.abs() < 1e-6
                    && sa.render_c.abs() < 1e-6
                    && sa.original_width > 0
                    && sa.original_height > 0
                {
                    Some((
                        sa.original_width as f64,
                        sa.original_height as f64,
                        sa.render_sx,
                        sa.render_sy,
                        sa.render_tx,
                        sa.render_ty,
                    ))
                } else {
                    None
                }
            };
            if let Some((ow, oh, msx, msy, mtx, mty)) = matrix {
                let x0 = mtx.min(mtx + ow * msx);
                let y0 = mty.min(mty + oh * msy);
                // 풀린 자식이 묶음이면 손자들의 행렬 이동값은 바깥 묶음 기준이라 새 기준점만큼 뺀다
                if let ShapeObject::Group(g) = &mut child {
                    fn shift(children: &mut [ShapeObject], dx: f64, dy: f64) {
                        for ch in children.iter_mut() {
                            let sa = match ch {
                                ShapeObject::Line(s) => &mut s.drawing.shape_attr,
                                ShapeObject::Rectangle(s) => &mut s.drawing.shape_attr,
                                ShapeObject::Ellipse(s) => &mut s.drawing.shape_attr,
                                ShapeObject::Arc(s) => &mut s.drawing.shape_attr,
                                ShapeObject::Polygon(s) => &mut s.drawing.shape_attr,
                                ShapeObject::Curve(s) => &mut s.drawing.shape_attr,
                                ShapeObject::Group(g) => &mut g.shape_attr,
                                ShapeObject::Picture(p) => &mut p.shape_attr,
                                ShapeObject::Chart(c) => &mut c.drawing.shape_attr,
                                ShapeObject::Ole(o) => &mut o.drawing.shape_attr,
                            };
                            sa.render_tx -= dx;
                            sa.render_ty -= dy;
                            if let ShapeObject::Group(g) = ch {
                                shift(&mut g.children, dx, dy);
                            }
                        }
                    }
                    shift(&mut g.children, x0, y0);
                }
                let c = child.common_mut();
                c.horizontal_offset = (group_x as f64 + x0).round() as i32 as u32;
                c.vertical_offset = (group_y as f64 + y0).round() as i32 as u32;
                c.width = (ow * msx).abs().round().max(1.0) as u32;
                c.height = (oh * msy).abs().round().max(1.0) as u32;
            }
            // 자식의 로컬 좌표를 글로벌 좌표로 변환 (그룹 스케일 적용)
            {
                let c = child.common_mut();
                if matrix.is_none() {
                c.horizontal_offset =
                    (group_x + (c.horizontal_offset as f64 * group_sx) as i32) as u32;
                c.vertical_offset = (group_y + (c.vertical_offset as f64 * group_sy) as i32) as u32;
                c.width = ((c.width as f64 * group_sx).round().max(1.0)) as u32;
                c.height = ((c.height as f64 * group_sy).round().max(1.0)) as u32;
                }
// ==== next ====
            // 도형별 좌표에 그룹 스케일 적용
            if group_sx != 1.0 || group_sy != 1.0 {
                Self::scale_shape_coords(&mut child, group_sx, group_sy);
            }
// ==== replace ====
            // 도형별 좌표에 그룹 스케일 적용
            // [claude-hwpx ungroup-matrix] 합성 행렬이 있으면 원래 좌표에 그 배율을 곱한다(묶음 배율이 이미 들어 있다)
            let (ksx, ksy) = matrix.map(|m| (m.2.abs(), m.3.abs())).unwrap_or((group_sx, group_sy));
            if ksx != 1.0 || ksy != 1.0 {
                Self::scale_shape_coords(&mut child, ksx, ksy);
            }
// ==== next ====
                sa.render_tx = 0.0;
                sa.render_ty = 0.0;
                sa.current_width = final_w;
// ==== replace ====
                sa.render_tx = 0.0;
                sa.render_ty = 0.0;
                // [claude-hwpx ungroup-matrix] 풀린 개체는 맨 위 개체라 묶음 안 배율을 남기지 않는다(크기는 common 에 확정)
                if matrix.is_some() {
                    sa.render_sx = 1.0;
                    sa.render_sy = 1.0;
                }
                sa.current_width = final_w;
