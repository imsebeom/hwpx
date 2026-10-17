"""개발용: 글자처럼 취급 표를 담은 줄 높이에 위, 아래 캡션의 높이와 캡션 간격을 더한다.

    python apply_tac_caption_line.py [--revert]

근거(d242 p8, p15): 한/글은 위 캡션 「(단위: 원)」(10pt 한 줄, 간격 283)이 달린 글자처럼 취급 표의 줄 높이를
「표 높이 + 바깥 여백 위아래 + 캡션 높이(마지막 줄 간격 제외) + 캡션 간격」으로 적는다(8412 + 283×2 + 1000 + 283 = 10261,
9839 + 140×2 + 1000 + 283 = 11402). 엔진은 캡션을 빼고 표 높이와 바깥 여백만 줄 높이로 써서 표마다 1,283 낮았다.
왼쪽, 오른쪽 캡션은 높이에 들지 않는다(측정기 height_measurer 와 같다).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx tac-caption-line]"
REL = "renderer/composer/line_breaking.rs"

EDITS = [
    (
        REL,
        "fn inline_control_line_height_hwp(para: &Paragraph) -> Option<i32> {\n",
        f"/// {TAG} 글자처럼 취급 표를 담은 줄 높이: 표 높이 + 바깥 여백 위아래 + 위, 아래 캡션(높이 + 캡션 간격).\n"
        "/// 한/글 재저장 d242: 8412 + 283×2 + 1000 + 283 = 10261. 왼쪽, 오른쪽 캡션은 높이에 들지 않는다.\n"
        "fn claude_tac_table_line_height_hwp(table: &crate::model::table::Table) -> i32 {\n"
        "    let base = table.common.height as i32\n"
        "        + table.outer_margin_top as i32\n"
        "        + table.outer_margin_bottom as i32;\n"
        "    let Some(caption) = table.caption.as_ref() else {\n"
        "        return base;\n"
        "    };\n"
        "    if matches!(\n"
        "        caption.direction,\n"
        "        crate::model::shape::CaptionDirection::Left | crate::model::shape::CaptionDirection::Right\n"
        "    ) {\n"
        "        return base;\n"
        "    }\n"
        "    // dpi 를 HWPUNIT 의 인치당 값(7200)으로 주면 px 대신 HWPUNIT 이 나온다\n"
        "    let caption_hu = crate::renderer::composer::caption_height_px(&table.caption, 7200.0).round() as i32;\n"
        "    if caption_hu <= 0 {\n"
        "        return base;\n"
        "    }\n"
        "    base + caption_hu + caption.spacing as i32\n"
        "}\n"
        "\n"
        "fn inline_control_line_height_hwp(para: &Paragraph) -> Option<i32> {\n",
    ),
    (
        REL,
        "            Control::Table(table) if table.common.treat_as_char => Some(\n"
        "                table.common.height as i32\n"
        "                    + table.outer_margin_top as i32\n"
        "                    + table.outer_margin_bottom as i32,\n"
        "            ),\n",
        "            Control::Table(table) if table.common.treat_as_char => {\n"
        "                Some(claude_tac_table_line_height_hwp(table))\n"
        "            }\n",
    ),
    (
        REL,
        "            (\n"
        "                width,\n"
        "                table.common.height as i32\n"
        "                    + table.outer_margin_top as i32\n"
        "                    + table.outer_margin_bottom as i32,\n"
        "            )\n",
        "            (width, claude_tac_table_line_height_hwp(table))\n",
    ),
    (
        REL,
        "            Control::Table(t) if t.common.treat_as_char => Some(\n"
        "                (t.common.height as i32)\n"
        "                    .saturating_add(i32::from(t.outer_margin_top))\n"
        "                    .saturating_add(i32::from(t.outer_margin_bottom)),\n"
        "            ),\n",
        "            Control::Table(t) if t.common.treat_as_char => Some(claude_tac_table_line_height_hwp(t)),\n",
    ),
    (
        "document_core/commands/document.rs",
        "                // 본문 NO_LS 텍스트 문단의 실폭 래핑은 composer recompose 가 담당한다.\n"
        "                if Self::needs_line_seg_reflow_in_scope(para, include_empty, section_sized) {\n",
        "                // 본문 NO_LS 텍스트 문단의 실폭 래핑은 composer recompose 가 담당한다.\n"
        "                // [claude-hwpx tac-caption-line] 표 캡션 문단도 줄 배치가 없으면 먼저 조판한다. 글자처럼 취급 표의 줄 높이가\n"
        "                // 캡션 높이를 쓰는데, 줄 배치 없는 캡션은 기본 400 으로 잡혀 한/글(10pt 캡션 1000)보다 낮았다(d242)\n"
        "                for ctrl in para.controls.iter_mut() {\n"
        "                    if let Control::Table(t) = ctrl {\n"
        "                        let cap_w = crate::renderer::hwpunit_to_px(t.common.width as i32, dpi);\n"
        "                        if let Some(cap) = t.caption.as_mut() {\n"
        "                            for cp in cap.paragraphs.iter_mut() {\n"
        "                                if Self::needs_line_seg_reflow_in_scope(cp, include_empty, section_sized) {\n"
        "                                    reflow_line_segs(cp, ParagraphBox::content_width_px(cap_w, dpi), styles, dpi);\n"
        "                                }\n"
        "                            }\n"
        "                        }\n"
        "                    }\n"
        "                }\n"
        "                if Self::needs_line_seg_reflow_in_scope(para, include_empty, section_sized) {\n",
    ),
    (
        "renderer/typeset.rs",
        "        let height_for_fit = if has_tac {\n"
        "            first_line_tac_height.unwrap_or(fmt.height_for_fit)\n"
        "        } else {\n",
        "        // [claude-hwpx tac-caption-line] 한 줄짜리 표 문단은 쪽 끝에서 문단 아래 간격 없이 「위 간격 + 줄 높이」만 들어가면\n"
        "        // 된다(한/글 e13 의 마지막 줄 규칙). 캡션을 넣어 줄 높이가 한/글과 같아지자 d221 의 쪽 높이 표(67846)가 아래\n"
        "        // 간격 6.7px 때문에 다음 쪽으로 밀렸다\n"
        "        let height_for_fit = if has_tac {\n"
        "            first_line_tac_height.unwrap_or(if fmt.line_heights.len() == 1 {\n"
        "                fmt.spacing_before + fmt.line_heights[0]\n"
        "            } else {\n"
        "                fmt.height_for_fit\n"
        "            })\n"
        "        } else {\n",
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
            sys.exit(f"{rel}: 자리 {n}곳 — {find[:50]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel)


if __name__ == "__main__":
    main()
