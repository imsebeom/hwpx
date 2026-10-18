// ==== find ====
    /// 비표준 lineseg 감지 (#177).
// ==== replace ====
    /// [claude-hwpx square-block] 옆에 글 자리가 없는 어울림 개체 무리를 자리 차지로 바꾸고 바꾼 개체의 instance id 를 돌려준다.
    fn claude_square_to_block(document: &mut crate::model::document::Document) -> Vec<u32> {
        use crate::model::control::Control;
        use crate::model::shape::{HorzAlign, HorzRelTo, TextWrap, VertRelTo};
        const MIN_GAP: i32 = 1000;
        let mut changed = Vec::new();
        for section in document.sections.iter_mut() {
            let pd = &section.section_def.page_def;
            let col = pd.width as i32 - pd.margin_left as i32 - pd.margin_right as i32;
            let multi = section.paragraphs.iter().any(|p| {
                p.controls
                    .iter()
                    .any(|c| matches!(c, Control::ColumnDef(cd) if cd.column_count > 1))
            });
            if col <= 0 || multi {
                continue;
            }
            for para in section.paragraphs.iter_mut() {
                // (컨트롤 번호, 왼, 오른, 위, 아래, 도형인지)
                let mut objs: Vec<(usize, i32, i32, i32, i32, bool)> = Vec::new();
                for (ci, ctrl) in para.controls.iter().enumerate() {
                    let (common, is_shape) = match ctrl {
                        Control::Shape(s) => (s.common(), true),
                        Control::Picture(p) => (&p.common, false),
                        _ => continue,
                    };
                    if common.treat_as_char
                        || common.text_wrap != TextWrap::Square
                        || common.vert_rel_to != VertRelTo::Para
                        || !matches!(common.horz_rel_to, HorzRelTo::Column | HorzRelTo::Para)
                        || common.instance_id == 0
                    {
                        continue;
                    }
                    let w = common.width as i32 + i32::from(common.margin.left) + i32::from(common.margin.right);
                    let off = common.horizontal_offset as i32;
                    let left = match common.horz_align {
                        HorzAlign::Left | HorzAlign::Inside => off,
                        HorzAlign::Right | HorzAlign::Outside => col - w - off,
                        HorzAlign::Center => (col - w) / 2 + off,
                    };
                    let top = common.vertical_offset as i32;
                    let h = common.height as i32 + i32::from(common.margin.top) + i32::from(common.margin.bottom);
                    objs.push((ci, left, left + w, top, top + h, is_shape));
                }
                if objs.is_empty() || !objs.iter().any(|o| o.5) {
                    continue;
                }
                let band_top = objs.iter().map(|o| o.3).max().unwrap_or(0);
                let band_bottom = objs.iter().map(|o| o.4).min().unwrap_or(0);
                if band_top >= band_bottom {
                    continue;
                }
                let mut spans: Vec<(i32, i32)> = objs.iter().map(|o| (o.1.max(0), o.2.min(col))).collect();
                spans.sort();
                let (mut gap, mut cur) = (0, 0);
                for (a, b) in spans {
                    if a > cur {
                        gap = gap.max(a - cur);
                    }
                    cur = cur.max(b);
                }
                gap = gap.max(col - cur);
                if gap >= MIN_GAP {
                    continue;
                }
                for o in &objs {
                    let common = match &mut para.controls[o.0] {
                        Control::Shape(s) => s.common_mut(),
                        Control::Picture(p) => &mut p.common,
                        _ => continue,
                    };
                    common.text_wrap = TextWrap::TopAndBottom;
                    changed.push(common.instance_id);
                }
            }
        }
        changed
    }

    /// [claude-hwpx square-block] 저장 사본에서 열 때 바꾼 개체를 원래 어울림으로 되돌린다(표 칸 안은 바꾸지 않으므로 본문만 본다).
    fn claude_restore_square(document: &mut crate::model::document::Document, ids: &[u32]) {
        use crate::model::control::Control;
        use crate::model::shape::TextWrap;
        for section in document.sections.iter_mut() {
            for para in section.paragraphs.iter_mut() {
                for ctrl in para.controls.iter_mut() {
                    let common = match ctrl {
                        Control::Shape(s) => s.common_mut(),
                        Control::Picture(p) => &mut p.common,
                        _ => continue,
                    };
                    if common.text_wrap == TextWrap::TopAndBottom && ids.contains(&common.instance_id) {
                        common.text_wrap = TextWrap::Square;
                    }
                }
            }
        }
    }

    /// 비표준 lineseg 감지 (#177).
// ==== next ====
        Self::reflow_zero_height_paragraphs(
            &mut document,
            &styles,
            DEFAULT_DPI,
            include_empty,
            include_cell_empty,
        );
        Self::clear_missing_lineseg_placeholders(&mut document);
// ==== replace ====
        // [claude-hwpx square-block] XML 출처(HWPX)만
        let claude_square_blocks = if use_xml_import_semantics {
            Self::claude_square_to_block(&mut document)
        } else {
            Vec::new()
        };
        Self::reflow_zero_height_paragraphs(
            &mut document,
            &styles,
            DEFAULT_DPI,
            include_empty,
            include_cell_empty,
        );
        Self::clear_missing_lineseg_placeholders(&mut document);
// ==== next ====
            claude_fn_cells: Vec::new(), // [claude-hwpx fn-cell-target]
        };
// ==== replace ====
            claude_fn_cells: Vec::new(), // [claude-hwpx fn-cell-target]
            claude_square_blocks, // [claude-hwpx square-block]
        };
// ==== next ====
        let serialized = if matches!(self.source_format, crate::parser::FileFormat::Hwp) {
            let mut doc = self.document.clone();
// ==== replace ====
        // [claude-hwpx square-block] 열 때 자리 차지로 바꾼 어울림 개체를 되돌린 사본으로 내보낸다
        let claude_restored = (!self.claude_square_blocks.is_empty()).then(|| {
            let mut d = self.document.clone();
            Self::claude_restore_square(&mut d, &self.claude_square_blocks);
            d
        });
        let claude_doc: &crate::model::document::Document =
            claude_restored.as_ref().unwrap_or(&self.document);
        let serialized = if matches!(self.source_format, crate::parser::FileFormat::Hwp) {
            let mut doc = claude_doc.clone();
// ==== next ====
        } else if hwp3_origin {
            let mut doc = self.document.clone();
            Self::push_hwp3_origin_marker(&mut doc);
            serialize(&doc)
        } else {
            serialize(&self.document)
        };
// ==== replace ====
        } else if hwp3_origin {
            let mut doc = claude_doc.clone();
            Self::push_hwp3_origin_marker(&mut doc);
            serialize(&doc)
        } else {
            serialize(claude_doc) // [claude-hwpx square-block]
        };
