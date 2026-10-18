"""개발용: 옆에 글 자리가 없는 어울림 개체 무리(도형 포함)를 열 때 자리 차지처럼 다룬다. 저장할 때는 원래 배치로 되돌린다.

    python apply_square_block.py [--revert]

한/글 사본 실험(exp/make_squarepair.py, d268 둘째 구역 p31 차트 둘): 어울림 개체들이 남긴 빈 자리마다 글이 흐르고(틈 5039 이상),
자리가 없으면(틈 39) 다음 문단이 개체 아래로 간다. 엔진은 어울림 도형(차트, OLE)을 흐름에서 전혀 비키지 않아 글이 차트 위에 겹치고
d268 이 한 쪽 늘었다. 이 패치는 「자리가 없는」 경우만 다룬다: 한 단짜리 구역에서, 같은 문단에 앵커된 글자처럼 취급하지 않는 어울림
개체(도형이 하나 이상 든 무리)가 세로로 겹치고, 단 폭에서 그 무리가 남긴 가장 넓은 빈 자리가 1000 HU 미만이면 자리 차지(TopAndBottom)로
바꿔 조판과 그리기의 기존 밀어내기를 탄다. 개체 instance id 를 기억해 HWPX 로 내보낼 때 원래 어울림으로 되돌린다.
그림만 든 무리(띠가 이미 다룸)와 instance id 가 0 인 개체는 건드리지 않는다. 옆으로 흐르는 경우(도형 띠)는 다루지 않는다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx square-block]"
DOC = "document_core/commands/document.rs"
MOD = "document_core/mod.rs"

FN = f"""    /// {TAG} 옆에 글 자리가 없는 어울림 개체 무리를 자리 차지로 바꾸고 바꾼 개체의 instance id 를 돌려준다.
    fn claude_square_to_block(document: &mut crate::model::document::Document) -> Vec<u32> {{
        use crate::model::control::Control;
        use crate::model::shape::{{HorzAlign, HorzRelTo, TextWrap, VertRelTo}};
        const MIN_GAP: i32 = 1000;
        let mut changed = Vec::new();
        for section in document.sections.iter_mut() {{
            let pd = &section.section_def.page_def;
            let col = pd.width as i32 - pd.margin_left as i32 - pd.margin_right as i32;
            let multi = section.paragraphs.iter().any(|p| {{
                p.controls
                    .iter()
                    .any(|c| matches!(c, Control::ColumnDef(cd) if cd.column_count > 1))
            }});
            if col <= 0 || multi {{
                continue;
            }}
            for para in section.paragraphs.iter_mut() {{
                // (컨트롤 번호, 왼, 오른, 위, 아래, 도형인지)
                let mut objs: Vec<(usize, i32, i32, i32, i32, bool)> = Vec::new();
                for (ci, ctrl) in para.controls.iter().enumerate() {{
                    let (common, is_shape) = match ctrl {{
                        Control::Shape(s) => (s.common(), true),
                        Control::Picture(p) => (&p.common, false),
                        _ => continue,
                    }};
                    if common.treat_as_char
                        || common.text_wrap != TextWrap::Square
                        || common.vert_rel_to != VertRelTo::Para
                        || !matches!(common.horz_rel_to, HorzRelTo::Column | HorzRelTo::Para)
                        || common.instance_id == 0
                    {{
                        continue;
                    }}
                    let w = common.width as i32 + i32::from(common.margin.left) + i32::from(common.margin.right);
                    let off = common.horizontal_offset as i32;
                    let left = match common.horz_align {{
                        HorzAlign::Left | HorzAlign::Inside => off,
                        HorzAlign::Right | HorzAlign::Outside => col - w - off,
                        HorzAlign::Center => (col - w) / 2 + off,
                    }};
                    let top = common.vertical_offset as i32;
                    let h = common.height as i32 + i32::from(common.margin.top) + i32::from(common.margin.bottom);
                    objs.push((ci, left, left + w, top, top + h, is_shape));
                }}
                if objs.is_empty() || !objs.iter().any(|o| o.5) {{
                    continue;
                }}
                let band_top = objs.iter().map(|o| o.3).max().unwrap_or(0);
                let band_bottom = objs.iter().map(|o| o.4).min().unwrap_or(0);
                if band_top >= band_bottom {{
                    continue;
                }}
                let mut spans: Vec<(i32, i32)> = objs.iter().map(|o| (o.1.max(0), o.2.min(col))).collect();
                spans.sort();
                let (mut gap, mut cur) = (0, 0);
                for (a, b) in spans {{
                    if a > cur {{
                        gap = gap.max(a - cur);
                    }}
                    cur = cur.max(b);
                }}
                gap = gap.max(col - cur);
                if gap >= MIN_GAP {{
                    continue;
                }}
                for o in &objs {{
                    let common = match &mut para.controls[o.0] {{
                        Control::Shape(s) => s.common_mut(),
                        Control::Picture(p) => &mut p.common,
                        _ => continue,
                    }};
                    common.text_wrap = TextWrap::TopAndBottom;
                    changed.push(common.instance_id);
                }}
            }}
        }}
        changed
    }}

    /// {TAG} 저장 사본에서 열 때 바꾼 개체를 원래 어울림으로 되돌린다(표 칸 안은 바꾸지 않으므로 본문만 본다).
    fn claude_restore_square(document: &mut crate::model::document::Document, ids: &[u32]) {{
        use crate::model::control::Control;
        use crate::model::shape::TextWrap;
        for section in document.sections.iter_mut() {{
            for para in section.paragraphs.iter_mut() {{
                for ctrl in para.controls.iter_mut() {{
                    let common = match ctrl {{
                        Control::Shape(s) => s.common_mut(),
                        Control::Picture(p) => &mut p.common,
                        _ => continue,
                    }};
                    if common.text_wrap == TextWrap::TopAndBottom && ids.contains(&common.instance_id) {{
                        common.text_wrap = TextWrap::Square;
                    }}
                }}
            }}
        }}
    }}

    /// 비표준 lineseg 감지 (#177).
"""

EDITS = [
    (DOC, "    /// 비표준 lineseg 감지 (#177).\n", FN),
    (
        DOC,
        """        Self::reflow_zero_height_paragraphs(
            &mut document,
            &styles,
            DEFAULT_DPI,
            include_empty,
            include_cell_empty,
        );
        Self::clear_missing_lineseg_placeholders(&mut document);
""",
        f"""        // {TAG} XML 출처(HWPX)만
        let claude_square_blocks = if use_xml_import_semantics {{
            Self::claude_square_to_block(&mut document)
        }} else {{
            Vec::new()
        }};
        Self::reflow_zero_height_paragraphs(
            &mut document,
            &styles,
            DEFAULT_DPI,
            include_empty,
            include_cell_empty,
        );
        Self::clear_missing_lineseg_placeholders(&mut document);
""",
    ),
    (
        DOC,
        "            claude_fn_cells: Vec::new(), // [claude-hwpx fn-cell-target]\n        };\n",
        "            claude_fn_cells: Vec::new(), // [claude-hwpx fn-cell-target]\n"
        f"            claude_square_blocks, // {TAG}\n        }};\n",
    ),
    (
        DOC,
        """        let serialized = if matches!(self.source_format, crate::parser::FileFormat::Hwp) {
            let mut doc = self.document.clone();
""",
        f"""        // {TAG} 열 때 자리 차지로 바꾼 어울림 개체를 되돌린 사본으로 내보낸다
        let claude_restored = (!self.claude_square_blocks.is_empty()).then(|| {{
            let mut d = self.document.clone();
            Self::claude_restore_square(&mut d, &self.claude_square_blocks);
            d
        }});
        let claude_doc: &crate::model::document::Document =
            claude_restored.as_ref().unwrap_or(&self.document);
        let serialized = if matches!(self.source_format, crate::parser::FileFormat::Hwp) {{
            let mut doc = claude_doc.clone();
""",
    ),
    (
        DOC,
        """        } else if hwp3_origin {
            let mut doc = self.document.clone();
            Self::push_hwp3_origin_marker(&mut doc);
            serialize(&doc)
        } else {
            serialize(&self.document)
        };
""",
        """        } else if hwp3_origin {
            let mut doc = claude_doc.clone();
            Self::push_hwp3_origin_marker(&mut doc);
            serialize(&doc)
        } else {
            serialize(claude_doc) // [claude-hwpx square-block]
        };
""",
    ),
    (
        MOD,
        "    pub(crate) claude_fn_cells: Vec<[usize; 5]>,\n}\n",
        "    pub(crate) claude_fn_cells: Vec<[usize; 5]>,\n"
        f"    /// {TAG} 열 때 어울림에서 자리 차지로 바꾼 개체의 instance id(내보낼 때 되돌린다)\n"
        "    pub(crate) claude_square_blocks: Vec<u32>,\n}\n",
    ),
    (
        MOD,
        "            claude_fn_cells: Vec::new(),\n        }\n",
        "            claude_fn_cells: Vec::new(),\n            claude_square_blocks: Vec::new(), // [claude-hwpx square-block]\n        }\n",
    ),
]


def main():
    revert = "--revert" in sys.argv
    edits = list(reversed(EDITS)) if revert else EDITS
    for rel, find, repl in edits:
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
