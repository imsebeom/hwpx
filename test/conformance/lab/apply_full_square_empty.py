"""개발용: HWPX 에서 줄 배치 없는 글 없는 문단에 열을 꽉 채우는 어울림(SQUARE) 표 하나만 있으면, 자리 차지 표처럼 흐름을
「바깥 위 여백 + 표 + 바깥 아래 여백」으로 잡는다(호스트 문단 아래 간격과 줄 간격은 표 아래에 묻힌다).

    python apply_full_square_empty.py [--revert]

한/글 새 조판 d027 p0(어울림 표 48190 + 여백 141x2, 줄 폭 48188, 높이 5173): 호스트 줄은 폭 0 으로 표 위, p1 = 5455 = 141 + 5173 + 141
(호스트 아래 간격 1000, 줄 간격 900 은 쓰지 않음). 같은 꼴 자리 차지 표(exp/harvest_emptyhost_line.py, 간격 있는 22개)도 모두 묻힌다.
엔진은 아래 간격 13.3 + 줄 간격 12.0 을 더하고 바깥 여백은 빼 21.6px 아래로 갔다(1쪽 글 전체 16~19pt 아래).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx full-square-empty]"

EDITS = [
    (
        "renderer/mod.rs",
        "pub(crate) fn para_has_no_stored_line_segs(p: &crate::model::paragraph::Paragraph) -> bool {\n"
        "    p.line_segs.is_empty() || p.line_segs.iter().all(|s| s.tag & 0x8000_0000 != 0)\n"
        "}\n",
        "pub(crate) fn para_has_no_stored_line_segs(p: &crate::model::paragraph::Paragraph) -> bool {\n"
        "    p.line_segs.is_empty() || p.line_segs.iter().all(|s| s.tag & 0x8000_0000 != 0)\n"
        "}\n"
        "\n"
        f"/// {TAG} 줄 배치 없는 글 없는 문단에 어울림 표(문단 기준) 하나만 있고, 표 너비 + 바깥 여백 좌우가 줄 폭 이상(옆에 글 자리 없음)\n"
        "pub(crate) fn claude_full_square_empty_host(\n"
        "    p: &crate::model::paragraph::Paragraph,\n"
        "    t: &crate::model::table::Table,\n"
        ") -> bool {\n"
        "    p.text.is_empty()\n"
        "        && para_has_no_stored_line_segs(p)\n"
        "        && !t.common.treat_as_char\n"
        "        && matches!(t.common.text_wrap, crate::model::shape::TextWrap::Square)\n"
        "        && matches!(t.common.vert_rel_to, crate::model::shape::VertRelTo::Para)\n"
        "        && p\n"
        "            .controls\n"
        "            .iter()\n"
        "            .filter(|c| {\n"
        "                matches!(\n"
        "                    c,\n"
        "                    crate::model::control::Control::Table(_)\n"
        "                        | crate::model::control::Control::Picture(_)\n"
        "                        | crate::model::control::Control::Shape(_)\n"
        "                )\n"
        "            })\n"
        "            .count()\n"
        "            == 1\n"
        "        && p.line_segs.first().is_some_and(|s| {\n"
        "            s.segment_width > 0\n"
        "                && t.common.width as i64 + t.outer_margin_left as i64 + t.outer_margin_right as i64\n"
        "                    >= s.segment_width as i64\n"
        "        })\n"
        "}\n",
    ),
    (
        "renderer/typeset.rs",
        "        let after = after\n            + self.claude_multi_float_host_line_px(para, ctrl_idx);\n",
        "        let after = after\n            + self.claude_multi_float_host_line_px(para, ctrl_idx);\n"
        f"        // {TAG} 열을 꽉 채우는 어울림 표의 빈 문단은 자리 차지 표처럼 바깥 여백만 쓰고 아래 간격, 줄 간격은 묻는다(d027 p0)\n"
        "        let (before, after) = if self.profile.get().hwpx_container()\n"
        "            && crate::renderer::claude_full_square_empty_host(para, table)\n"
        "        {\n"
        "            (\n"
        "                hwpunit_to_px(table.outer_margin_top as i32, self.dpi),\n"
        "                hwpunit_to_px(table.outer_margin_bottom as i32, self.dpi),\n"
        "            )\n"
        "        } else {\n"
        "            (before, after)\n"
        "        };\n",
    ),
    (
        "renderer/layout.rs",
        "                        Control::Table(t)\n"
        "                            if is_para_topbottom_float(&t.common) && !para_has_visible_text(para)\n"
        "                    )\n"
        "                })\n"
        "                .unwrap_or(false);\n",
        "                        Control::Table(t)\n"
        "                            if is_para_topbottom_float(&t.common) && !para_has_visible_text(para)\n"
        "                    )\n"
        f"                    // {TAG} 열을 꽉 채우는 어울림 표의 빈 문단은 자리 차지 표처럼 그린다(d027 p0)\n"
        "                    || (self.profile.get().hwpx_container()\n"
        "                        && matches!(c, Control::Table(t)\n"
        "                            if crate::renderer::claude_full_square_empty_host(para, t)))\n"
        "                })\n"
        "                .unwrap_or(false);\n",
    ),
    (
        "renderer/layout.rs",
        "                if let Some(para_style) = styles.para_styles.get(para_style_id) {\n"
        "                    if para_style.spacing_after > 0.0 {\n"
        "                        y_offset += para_style.spacing_after;\n",
        "                if let Some(para_style) = styles.para_styles.get(para_style_id) {\n"
        f"                    // {TAG} 열을 꽉 채우는 어울림 표의 빈 문단은 아래 간격이 표 아래에 묻힌다\n"
        "                    let claude_full_square = self.profile.get().hwpx_container()\n"
        "                        && matches!(para.controls.get(control_index), Some(Control::Table(t))\n"
        "                            if crate::renderer::claude_full_square_empty_host(para, t));\n"
        "                    if para_style.spacing_after > 0.0 && !claude_full_square {\n"
        "                        y_offset += para_style.spacing_after;\n",
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
