"""개발용: 개체 풀기가 자식의 위치와 크기를 그리기와 같은 합성 행렬로 정한다.

    python apply_ungroup_matrix.py [--revert]

사용자 보고(2026-10-23, 워크시트 hwp): 「1 교육과정 분석에서 시작하기」 묶음을 풀자 개체가 커졌다. 그림 자식은 원래 크기 148560 x 9480 에
행렬 배율 0.333 x 0.324 를 곱해 그려지는데(묶음 폭 49400 과 같음), 풀기는 행렬을 무시하고 원래 크기 x 묶음 배율(1.048)로 155688 을 만들었다.
글상자 사각형(「교육과정 분석에서 시작하기」)도 행렬 배율 12.861 이 빠져 3421 로 줄었다.
고침: 자식의 합성 행렬(render_sx/sy/tx/ty, 묶음 배율 포함)이 있고 회전이 없으면 위치 = 묶음 위치 + min(tx, tx + 원래 폭 x sx),
크기 = |원래 크기 x 배율|, 도형 내부 좌표는 |배율| 로 늘린다. 풀린 자식이 묶음이면 그 손자들의 행렬 이동값에서 새 기준점을 뺀다.
행렬이 없거나 회전이 있으면 종전 계산.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx ungroup-matrix]"
F = "document_core/commands/object_ops/shape.rs"

EDITS = [
    (
        F,
        "            // 자식의 로컬 좌표를 글로벌 좌표로 변환 (그룹 스케일 적용)\n"
        "            {\n"
        "                let c = child.common_mut();\n"
        "                c.horizontal_offset =\n"
        "                    (group_x + (c.horizontal_offset as f64 * group_sx) as i32) as u32;\n"
        "                c.vertical_offset = (group_y + (c.vertical_offset as f64 * group_sy) as i32) as u32;\n"
        "                c.width = ((c.width as f64 * group_sx).round().max(1.0)) as u32;\n"
        "                c.height = ((c.height as f64 * group_sy).round().max(1.0)) as u32;\n",
        f"            // {TAG} 그리기와 같은 합성 행렬(묶음 배율 포함)이 있고 회전이 없으면 그것으로 위치와 크기를 정한다\n"
        "            let matrix = {\n"
        "                let sa = child.shape_attr();\n"
        "                if sa.render_sx.abs() > 1e-9\n"
        "                    && sa.render_sy.abs() > 1e-9\n"
        "                    && sa.render_b.abs() < 1e-6\n"
        "                    && sa.render_c.abs() < 1e-6\n"
        "                    && sa.original_width > 0\n"
        "                    && sa.original_height > 0\n"
        "                {\n"
        "                    Some((\n"
        "                        sa.original_width as f64,\n"
        "                        sa.original_height as f64,\n"
        "                        sa.render_sx,\n"
        "                        sa.render_sy,\n"
        "                        sa.render_tx,\n"
        "                        sa.render_ty,\n"
        "                    ))\n"
        "                } else {\n"
        "                    None\n"
        "                }\n"
        "            };\n"
        "            if let Some((ow, oh, msx, msy, mtx, mty)) = matrix {\n"
        "                let x0 = mtx.min(mtx + ow * msx);\n"
        "                let y0 = mty.min(mty + oh * msy);\n"
        "                // 풀린 자식이 묶음이면 손자들의 행렬 이동값은 바깥 묶음 기준이라 새 기준점만큼 뺀다\n"
        "                if let ShapeObject::Group(g) = &mut child {\n"
        "                    fn shift(children: &mut [ShapeObject], dx: f64, dy: f64) {\n"
        "                        for ch in children.iter_mut() {\n"
        "                            let sa = match ch {\n"
        "                                ShapeObject::Line(s) => &mut s.drawing.shape_attr,\n"
        "                                ShapeObject::Rectangle(s) => &mut s.drawing.shape_attr,\n"
        "                                ShapeObject::Ellipse(s) => &mut s.drawing.shape_attr,\n"
        "                                ShapeObject::Arc(s) => &mut s.drawing.shape_attr,\n"
        "                                ShapeObject::Polygon(s) => &mut s.drawing.shape_attr,\n"
        "                                ShapeObject::Curve(s) => &mut s.drawing.shape_attr,\n"
        "                                ShapeObject::Group(g) => &mut g.shape_attr,\n"
        "                                ShapeObject::Picture(p) => &mut p.shape_attr,\n"
        "                                ShapeObject::Chart(c) => &mut c.drawing.shape_attr,\n"
        "                                ShapeObject::Ole(o) => &mut o.drawing.shape_attr,\n"
        "                            };\n"
        "                            sa.render_tx -= dx;\n"
        "                            sa.render_ty -= dy;\n"
        "                            if let ShapeObject::Group(g) = ch {\n"
        "                                shift(&mut g.children, dx, dy);\n"
        "                            }\n"
        "                        }\n"
        "                    }\n"
        "                    shift(&mut g.children, x0, y0);\n"
        "                }\n"
        "                let c = child.common_mut();\n"
        "                c.horizontal_offset = (group_x as f64 + x0).round() as i32 as u32;\n"
        "                c.vertical_offset = (group_y as f64 + y0).round() as i32 as u32;\n"
        "                c.width = (ow * msx).abs().round().max(1.0) as u32;\n"
        "                c.height = (oh * msy).abs().round().max(1.0) as u32;\n"
        "            }\n"
        "            // 자식의 로컬 좌표를 글로벌 좌표로 변환 (그룹 스케일 적용)\n"
        "            {\n"
        "                let c = child.common_mut();\n"
        "                if matrix.is_none() {\n"
        "                c.horizontal_offset =\n"
        "                    (group_x + (c.horizontal_offset as f64 * group_sx) as i32) as u32;\n"
        "                c.vertical_offset = (group_y + (c.vertical_offset as f64 * group_sy) as i32) as u32;\n"
        "                c.width = ((c.width as f64 * group_sx).round().max(1.0)) as u32;\n"
        "                c.height = ((c.height as f64 * group_sy).round().max(1.0)) as u32;\n"
        "                }\n",
    ),
    (
        F,
        "            // 도형별 좌표에 그룹 스케일 적용\n"
        "            if group_sx != 1.0 || group_sy != 1.0 {\n"
        "                Self::scale_shape_coords(&mut child, group_sx, group_sy);\n"
        "            }\n",
        "            // 도형별 좌표에 그룹 스케일 적용\n"
        f"            // {TAG} 합성 행렬이 있으면 원래 좌표에 그 배율을 곱한다(묶음 배율이 이미 들어 있다)\n"
        "            let (ksx, ksy) = matrix.map(|m| (m.2.abs(), m.3.abs())).unwrap_or((group_sx, group_sy));\n"
        "            if ksx != 1.0 || ksy != 1.0 {\n"
        "                Self::scale_shape_coords(&mut child, ksx, ksy);\n"
        "            }\n",
    ),
    (
        F,
        "                sa.render_tx = 0.0;\n"
        "                sa.render_ty = 0.0;\n"
        "                sa.current_width = final_w;\n",
        "                sa.render_tx = 0.0;\n"
        "                sa.render_ty = 0.0;\n"
        f"                // {TAG} 풀린 개체는 맨 위 개체라 묶음 안 배율을 남기지 않는다(크기는 common 에 확정)\n"
        "                if matrix.is_some() {\n"
        "                    sa.render_sx = 1.0;\n"
        "                    sa.render_sy = 1.0;\n"
        "                }\n"
        "                sa.current_width = final_w;\n",
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
