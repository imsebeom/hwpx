"""개발용: 쪽 영역 안으로 제한(flowWithText=1) + 나누지 않음 인 빈 문단 위아래 배치 표가 남은 자리에 안 들어가면 미루고, 뒤 글이 지금 쪽을 채운다.

    python apply_restrict_float_defer.py [--revert]

한/글 2024 실측(2026-10-19, 가이드북 3장 _261019_19 사본의 그림 3-2 표에 restrictInPage 만 켬, 한/글 PDF):
3쪽에 앵커 빈 문단이 빈 줄 한 줄(21.3px = 줄 1000 + 간격 600)로 남고 뒤 문단(「2) 서비스 내에…」, 「백엔드 코드가…」 첫 줄)이
3쪽을 끝까지 채운다. 표는 4쪽 본문 맨 위(바깥 위 여백 3.8px 아래)에 놓이고, 3쪽에서 넘어온 문단의 나머지 줄이 표 아래에서 잇는다.
엔진은 앵커 문단째 4쪽으로 넘겨 3쪽 아래가 비고 글 순서가 한/글과 달랐다. 조건은 실측한 꼴로 좁힌다(글자처럼 취급 아님,
문단 기준, 위아래 배치, 오프셋 0, 문단에 개체가 이 표 하나, 새 쪽에는 들어감). 미룬 표는 기존 장치(deferred_table_controls,
d322 공동 앵커 표)로 새 쪽 맨 위에 꺼내고, 글 문단 안에서 쪽이 넘어갈 때도 꺼낸다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx restrict-float-defer]"

FLUSH = (
    "            if st.profile.hwpx_container()\n"
    "                && !st.deferred_table_controls.is_empty()\n"
    "                && st.current_items.is_empty()\n"
    "            {\n"
    "                self.flush_deferred_table_controls(st, paragraphs, claude_composed, styles, claude_measured, None);\n"
    "            }\n"
)

EDITS = [
    (
        "renderer/typeset.rs",
        "                        // [claude-hwpx defer-coanchored-fresh] 같은 문단 뒤쪽 공동 앵커 표가 남은 자리에 안 들어가고 새 쪽에는 들어가면 미룬다(d322 p77 체육과 표)\n",
        f"                        // {TAG} 쪽 영역 제한 + 나누지 않음 빈 문단 표 하나가 남은 자리에 안 들어가면 미루고 앵커 줄만 이 쪽에 남긴다(한/글 실측, 가이드북 3장 그림 3-2)\n"
        "                        if st.profile.hwpx_container()\n"
        "                            && st.col_count == 1\n"
        "                            && order_pos == 0\n"
        "                            && !st.current_items.is_empty()\n"
        "                            && self.claude_is_restrict_float_defer_table(para, table, &fmt)\n"
        "                            && {\n"
        "                                let claude_h = ft.effective_height + ft.host_spacing.before;\n"
        "                                claude_h > st.available_height() - st.current_height\n"
        "                                    && claude_h <= st.base_available_height()\n"
        "                            }\n"
        "                        {\n"
        "                            st.deferred_table_controls.push(DeferredTableControl {\n"
        "                                para_index: para_idx,\n"
        "                                control_index: ctrl_idx,\n"
        "                                is_first_placed,\n"
        "                                is_last_placed,\n"
        "                                para_start_height,\n"
        "                            });\n"
        "                            st.current_height += para\n"
        "                                .line_segs\n"
        "                                .first()\n"
        "                                .map(|s| hwpunit_to_px(s.line_height + s.line_spacing.max(0), self.dpi))\n"
        "                                .unwrap_or(0.0);\n"
        "                            continue;\n"
        "                        }\n"
        "                        // [claude-hwpx defer-coanchored-fresh] 같은 문단 뒤쪽 공동 앵커 표가 남은 자리에 안 들어가고 새 쪽에는 들어가면 미룬다(d322 p77 체육과 표)\n",
    ),
    (
        "renderer/typeset.rs",
        "    fn is_coanchored_rowbreak_split_trigger_table(\n",
        f"    /// {TAG} 미룰 수 있는 쪽 영역 제한 표: 글 없는 문단의 유일한 개체, 문단 기준 위아래 배치, 나누지 않음, 오프셋 0\n"
        "    fn claude_is_restrict_float_defer_table(\n"
        "        &self,\n"
        "        para: &Paragraph,\n"
        "        table: &crate::model::table::Table,\n"
        "        fmt: &FormattedParagraph,\n"
        "    ) -> bool {\n"
        "        use crate::model::shape::{TextWrap, VertRelTo};\n"
        "\n"
        "        self.profile.get().hwpx_container()\n"
        "            && !para_has_visible_text(para)\n"
        "            && para\n"
        "                .controls\n"
        "                .iter()\n"
        "                .filter(|c| matches!(c, Control::Table(_) | Control::Picture(_) | Control::Shape(_)))\n"
        "                .count()\n"
        "                == 1\n"
        "            && !self.is_effective_tac_table(para, table, fmt)\n"
        "            && !table.common.treat_as_char\n"
        "            && table.common.flow_with_text\n"
        "            && matches!(table.common.text_wrap, TextWrap::TopAndBottom)\n"
        "            && matches!(table.common.vert_rel_to, VertRelTo::Para)\n"
        "            && matches!(table.page_break, crate::model::table::TablePageBreak::None)\n"
        "            && signed_hwpunit(table.common.vertical_offset) == 0\n"
        "    }\n"
        "\n"
        "    fn is_coanchored_rowbreak_split_trigger_table(\n",
    ),
    (
        "renderer/typeset.rs",
        "            if !self.is_deferred_coanchored_rowbreak_table(para, table, &fmt) {\n"
        "                continue;\n"
        "            }\n",
        f"            // {TAG} 쪽 영역 제한 표도 꺼낸다\n"
        "            if !self.is_deferred_coanchored_rowbreak_table(para, table, &fmt)\n"
        "                && !self.claude_is_restrict_float_defer_table(para, table, &fmt)\n"
        "            {\n"
        "                continue;\n"
        "            }\n",
    ),
    (
        "renderer/typeset.rs",
        "        styles: &ResolvedStyleSet,\n"
        "        is_last_in_section: bool,\n"
        "    ) {\n"
        "        // [#2243 진단] 문단 진입 시 누적 높이",
        "        styles: &ResolvedStyleSet,\n"
        "        is_last_in_section: bool,\n"
        f"        // {TAG} 글 문단이 쪽을 넘길 때 미룬 표를 꺼내려고 받는다\n"
        "        claude_composed: &[ComposedParagraph],\n"
        "        claude_measured: &[MeasuredTable],\n"
        "    ) {\n"
        "        // [#2243 진단] 문단 진입 시 누적 높이",
    ),
    (
        "renderer/typeset.rs",
        "                    &formatted,\n"
        "                    paragraphs,\n"
        "                    styles,\n"
        "                    is_last_in_section,\n"
        "                );\n",
        "                    &formatted,\n"
        "                    paragraphs,\n"
        "                    styles,\n"
        "                    is_last_in_section,\n"
        f"                    composed, // {TAG}\n"
        "                    measured_tables,\n"
        "                );\n",
    ),
    (
        "renderer/typeset.rs",
        "            && !hwp_first_line_before_reset_fits\n"
        "        {\n"
        "            st.advance_column_or_new_page();\n"
        "        }\n",
        "            && !hwp_first_line_before_reset_fits\n"
        "        {\n"
        "            st.advance_column_or_new_page();\n"
        f"            // {TAG} 새 쪽 맨 위에 미룬 표부터\n"
        + FLUSH.replace("            ", "            ", 1)
        + "        }\n",
    ),
    (
        "renderer/typeset.rs",
        "                {\n"
        "                    st.advance_column_or_new_page();\n"
        "                    continue;\n"
        "                }\n"
        "                st.current_items.push(PageItem::FullParagraph {\n",
        "                {\n"
        "                    st.advance_column_or_new_page();\n"
        f"                    // {TAG} 새 쪽 맨 위에 미룬 표부터\n"
        + "".join("        " + ln + "\n" for ln in FLUSH.rstrip("\n").split("\n"))
        + "                    continue;\n"
        "                }\n"
        "                st.current_items.push(PageItem::FullParagraph {\n",
    ),
    (
        "renderer/typeset.rs",
        "            // move: 나머지 줄 → 다음 단/페이지\n"
        "            st.advance_column_or_new_page();\n"
        "            cursor_line = end_line;\n",
        "            // move: 나머지 줄 → 다음 단/페이지\n"
        "            st.advance_column_or_new_page();\n"
        f"            // {TAG} 3쪽에서 시작한 문단의 나머지 줄은 4쪽의 미룬 표 아래에서 잇는다(한/글 실측)\n"
        + FLUSH
        + "            cursor_line = end_line;\n",
    ),
    (
        "renderer/typeset.rs",
        "                    .max(0.0)\n"
        "            } else {\n"
        "                base_available\n"
        "            };\n",
        "                    .max(0.0)\n"
        f"            }} else if st.profile.hwpx_container()\n"
        "                && st.current_height > 0.0\n"
        "                && matches!(st.current_items.first(), Some(PageItem::Table { .. } | PageItem::PartialTable { .. }))\n"
        "            {\n"
        f"                // {TAG} 이어지는 줄 앞에 미룬 표를 놓았으면 그 높이와 각주 자리를 뺀다\n"
        "                (base_available - st.current_footnote_height - fn_margin - st.current_height).max(0.0)\n"
        "            } else {\n"
        "                base_available\n"
        "            };\n",
    ),
    (
        "renderer/typeset.rs",
        "                    if self.is_effective_tac_table(para, table, &fmt) {\n",
        f"                    // {TAG} 미룬 표가 있고 이 표(글자처럼 취급이거나 나누지 않음)가 남은 자리에 안 들어가 새 쪽으로 가면\n"
        "                    // 새 쪽에 미룬 표부터 놓는다(한/글 실측: 2-4 원고 사본, 그림 4-6 다음 「예시 프롬프트」 상자)\n"
        "                    if st.profile.hwpx_container()\n"
        "                        && st.col_count == 1\n"
        "                        && !st.deferred_table_controls.is_empty()\n"
        "                        && st.deferred_table_controls.iter().all(|d| d.para_index < para_idx)\n"
        "                        && (self.is_effective_tac_table(para, table, &fmt)\n"
        "                            || matches!(table.page_break, crate::model::table::TablePageBreak::None))\n"
        "                    {\n"
        "                        let claude_h = ft.effective_height + ft.host_spacing.before;\n"
        "                        // 표 문단이 이미 새 쪽으로 넘어왔으면 바로, 아니면 이 표가 안 들어갈 때 쪽을 넘기고 꺼낸다\n"
        "                        if !st.current_items.is_empty()\n"
        "                            && claude_h > st.available_height() - st.current_height\n"
        "                            && claude_h <= st.base_available_height()\n"
        "                        {\n"
        "                            st.advance_column_or_new_page();\n"
        "                        }\n"
        "                        if st.current_items.is_empty() {\n"
        "                            self.flush_deferred_table_controls(st, paragraphs_all, composed_all, styles, measured_tables, None);\n"
        "                        }\n"
        "                    }\n"
        "                    if self.is_effective_tac_table(para, table, &fmt) {\n",
    ),
    (
        "renderer/typeset.rs",
        "        let strict_after_empty_host_float = take_strict_plain_text_fit_after_empty_host_float_once(\n",
        f"        // {TAG} 이 문단 앞에서 쪽이 이미 넘어가 비었으면 미룬 표부터(문단 시작 훅 뒤에 넘기는 규칙이 있다, 2-4 사본 p58)\n"
        "        if st.profile.hwpx_container()\n"
        "            && !st.deferred_table_controls.is_empty()\n"
        "            && st.current_items.is_empty()\n"
        "        {\n"
        "            self.flush_deferred_table_controls(st, paragraphs, claude_composed, styles, claude_measured, None);\n"
        "        }\n"
        "        let strict_after_empty_host_float = take_strict_plain_text_fit_after_empty_host_float_once(\n",
    ),
    (
        "renderer/layout.rs",
        "                y_offset = hcursor.vpos_adjust(y_offset, item_para, paragraphs, styles);\n",
        f"                // {TAG} 단 첫 항목이 미룬 표면(다음 항목이 앞 쪽에서 이어지는 줄이거나 표 문단보다 두 칸 이상 뒤)\n"
        "                // 앵커 문단의 저장 위치는 앞 쪽 것이다 — 그 vpos 로 스냅하지 않고 표 아래로 순서대로 잇는다\n"
        "                if self.profile.get().hwpx_container()\n"
        "                    && item_ordinal == 1\n"
        "                    && matches!(\n"
        "                        col_content.items.first(),\n"
        "                        Some(PageItem::Table { para_index, .. } | PageItem::PartialTable { para_index, .. })\n"
        "                            if *para_index < item_para\n"
        "                                && (*para_index + 1 < item_para\n"
        "                                    || matches!(item, PageItem::PartialParagraph { start_line, .. } if *start_line > 0))\n"
        "                    )\n"
        "                {\n"
        "                    hcursor.prev_layout_para = None;\n"
        "                }\n"
        "                y_offset = hcursor.vpos_adjust(y_offset, item_para, paragraphs, styles);\n",
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
