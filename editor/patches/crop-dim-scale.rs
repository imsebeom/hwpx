// ==== find ====
    fn picture_crop_ui_amounts(pic: &crate::model::image::Picture) -> (i32, i32, i32, i32) {
        let (extent_w, extent_h) = Self::picture_crop_extent_hu(pic);
        let left = pic.crop.left.max(0);
        let top = pic.crop.top.max(0);
        let right = if extent_w > 0 && pic.crop.right > left {
            (extent_w - pic.crop.right).max(0)
        } else {
            0
        };
        let bottom = if extent_h > 0 && pic.crop.bottom > top {
            (extent_h - pic.crop.bottom).max(0)
        } else {
            0
        };
        (left, top, right, bottom)
    }
    fn set_picture_crop_from_ui_amounts(
        pic: &mut crate::model::image::Picture,
        left: i32,
        top: i32,
        right: i32,
        bottom: i32,
    ) {
        let (extent_w, extent_h) = Self::picture_crop_extent_hu(pic);
        pic.crop.left = left.max(0);
        pic.crop.top = top.max(0);
        if extent_w > 0 {
            pic.crop.right = (extent_w - right.max(0)).max(pic.crop.left);
        } else {
            pic.crop.right = right.max(0);
        }
        if extent_h > 0 {
            pic.crop.bottom = (extent_h - bottom.max(0)).max(pic.crop.top);
        } else {
            pic.crop.bottom = bottom.max(0);
        }
    }
// ==== replace ====
    // [claude-hwpx crop-dim-scale] 자르기 값(속성 API 의 cropLeft..Bottom)은 원본 크기(orgSz) 단위이고, 저장되는 imgClip 은
    // imgDim 단위다. 둘이 다른 그림(한/글 저장본의 1.5배, 에디터가 넣은 그림은 orgSz=화면 크기라 12배쯤)에서
    // 단위를 섞어 자르면 imgClip 이 엉뚱한 곳을 가리켜 그림이 크게 확대돼 보였다(2026-10-21 결과보고서 사진 자르기).
    // imgDim 이 있으면 그 비율로 바꿔 읽고 쓴다. 없으면 종전대로 원본 크기를 범위로 쓴다.
    fn claude_crop_scale(pic: &crate::model::image::Picture) -> (i32, i32, f64, f64) {
        let (ow, oh) = Self::picture_crop_extent_hu(pic);
        match pic.crop_reference_size() {
            Some((dw, dh)) if ow > 0 && oh > 0 => {
                (dw as i32, dh as i32, dw as f64 / ow as f64, dh as f64 / oh as f64)
            }
            _ => (ow, oh, 1.0, 1.0),
        }
    }
    fn picture_crop_ui_amounts(pic: &crate::model::image::Picture) -> (i32, i32, i32, i32) {
        let (extent_w, extent_h, sx, sy) = Self::claude_crop_scale(pic);
        let ui = |v: i32, s: f64| ((v.max(0) as f64) / s).round() as i32;
        let left = ui(pic.crop.left, sx);
        let top = ui(pic.crop.top, sy);
        let right = if extent_w > 0 && pic.crop.right > pic.crop.left.max(0) {
            ui(extent_w - pic.crop.right, sx)
        } else {
            0
        };
        let bottom = if extent_h > 0 && pic.crop.bottom > pic.crop.top.max(0) {
            ui(extent_h - pic.crop.bottom, sy)
        } else {
            0
        };
        (left, top, right, bottom)
    }
    fn set_picture_crop_from_ui_amounts(
        pic: &mut crate::model::image::Picture,
        left: i32,
        top: i32,
        right: i32,
        bottom: i32,
    ) {
        let (extent_w, extent_h, sx, sy) = Self::claude_crop_scale(pic);
        let clip = |v: i32, s: f64| ((v.max(0) as f64) * s).round() as i32;
        pic.crop.left = clip(left, sx);
        pic.crop.top = clip(top, sy);
        if extent_w > 0 {
            pic.crop.right = (extent_w - clip(right, sx)).max(pic.crop.left);
        } else {
            pic.crop.right = right.max(0);
        }
        if extent_h > 0 {
            pic.crop.bottom = (extent_h - clip(bottom, sy)).max(pic.crop.top);
        } else {
            pic.crop.bottom = bottom.max(0);
        }
    }
