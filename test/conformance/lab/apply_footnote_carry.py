"""개발용: HWPX 에서 표 칸 각주가 그 쪽 아래에 들어가지 않으면 다음 쪽 각주 영역으로 넘긴다(표는 첫 각주만 들어가면 그 쪽에 둔다).

    python apply_footnote_carry.py [--revert]

근거(2026-10-18 가이드북 2장 원고 _44 를 한/글로 열어 PDF 로 저장): 6쪽 표(4x3, 글자처럼 취급)의 칸 안 각주 넷 가운데 한/글은
1), 2) 만 6쪽 아래에 두고 3), 4) 는 7쪽 아래로 넘긴다(두 쪽 모두 각주 시작 969.6px). 표와 캡션은 그대로 6쪽 끝과 7쪽 머리에 둔다.
엔진은 각주를 그 쪽에 모두 올려 표, 캡션과 겹쳐 그렸고(줄 배치 없는 각주를 400 HU 로 셀 때), 각주 높이를 바로 재면(footnote-reflow)
표 전체를 7쪽으로 보내 쪽이 하나 늘었다(정답본 d327 도 9 -> 10쪽). 나뉘는 표(RowBreak)에는 이미 칸 각주 대기열이 있어
(register_queued_table_footnotes) 글자처럼 취급 표 경로에만 같은 동작을 넣는다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx footnote-carry]"

EDITS = [
    (
        "renderer/typeset.rs",
        "    reset_vpos_after_queued_table_footnote_page: bool,\n",
        "    reset_vpos_after_queued_table_footnote_page: bool,\n"
        f"    /// {TAG} 이 쪽 아래에 들어가지 않아 다음 쪽 각주 영역 맨 앞으로 넘길 표 칸 각주(각주, 높이)\n"
        "    claude_carry_notes: Vec<(crate::renderer::pagination::FootnoteRef, f64)>,\n",
    ),
    (
        "renderer/typeset.rs",
        "            reset_vpos_after_queued_table_footnote_page: false,\n",
        "            reset_vpos_after_queued_table_footnote_page: false,\n"
        "            claude_carry_notes: Vec::new(),\n",
    ),
    (
        "renderer/typeset.rs",
        "        self.pages.push(self.new_page_content(Vec::new()));\n        self.reset_for_new_page();\n",
        "        self.pages.push(self.new_page_content(Vec::new()));\n        self.reset_for_new_page();\n"
        f"        // {TAG} 앞 쪽에 들어가지 않아 넘긴 표 칸 각주를 이 쪽 각주 영역 맨 앞에 둔다. 한/글은 넘긴 각주 자리를 이 쪽 본문에서\n"
        "        // 비우지 않는다(가이드북 2장 7쪽: 본문 줄 981.5, 1003.1 과 각주 줄 969.6~1016.5 가 겹쳐 그려짐) — 쪽 나눔을 맞추려 높이는 예약하지 않는다\n"
        "        for (note, _height) in std::mem::take(&mut self.claude_carry_notes) {\n"
        "            if let Some(page) = self.pages.last_mut() {\n"
        "                page.footnotes.push(note);\n"
        "            }\n"
        "        }\n",
    ),
    (
        "renderer/typeset.rs",
        "                let projected =\n"
        "                    st.projected_footnote_height(ft.table_footnote_height, ft.table_footnote_count);\n"
        "                let extra = (projected - reclaim).max(0.0) - (st.current_footnote_height - reclaim).max(0.0);\n",
        f"                // {TAG} HWPX 는 첫 각주만 들어가면 표를 이 쪽에 두고 나머지 각주는 다음 쪽으로 넘긴다(가이드북 2장 표 2-1)\n"
        "                let projected = if st.profile.hwpx_container() {\n"
        "                    let first = ft\n"
        "                        .table_footnotes\n"
        "                        .first()\n"
        "                        .map(|note| note.content_height)\n"
        "                        .unwrap_or(ft.table_footnote_height);\n"
        "                    st.projected_footnote_height(first, 1)\n"
        "                } else {\n"
        "                    st.projected_footnote_height(ft.table_footnote_height, ft.table_footnote_count)\n"
        "                };\n"
        "                let extra = (projected - reclaim).max(0.0) - (st.current_footnote_height - reclaim).max(0.0);\n",
    ),
    (
        "renderer/typeset.rs",
        "                    // 표 셀 내 각주 수집 (Paginator engine.rs:679-701 동일)\n"
        "                    if !st\n"
        "                        .fragment_queued_table_footnotes\n"
        "                        .contains(&(para_idx, ctrl_idx))\n"
        "                    {\n"
        "                        for (cell_idx, cell) in table.cells.iter().enumerate() {\n"
        "                            for (cp_idx, cp) in cell.paragraphs.iter().enumerate() {\n"
        "                                for (cc_idx, cc) in cp.controls.iter().enumerate() {\n"
        "                                    if let Control::Footnote(fn_ctrl) = cc {\n"
        "                                        self.register_unqueued_table_footnote(\n"
        "                                            st,\n"
        "                                            fn_ctrl,\n"
        "                                            FootnoteSource::TableCell {\n"
        "                                                para_index: para_idx,\n"
        "                                                table_control_index: ctrl_idx,\n"
        "                                                cell_index: cell_idx,\n"
        "                                                cell_para_index: cp_idx,\n"
        "                                                cell_control_index: cc_idx,\n"
        "                                            },\n"
        "                                        );\n"
        "                                    }\n",
        "                    // 표 셀 내 각주 수집 (Paginator engine.rs:679-701 동일)\n"
        "                    if !st\n"
        "                        .fragment_queued_table_footnotes\n"
        "                        .contains(&(para_idx, ctrl_idx))\n"
        "                    {\n"
        "                        for (cell_idx, cell) in table.cells.iter().enumerate() {\n"
        "                            for (cp_idx, cp) in cell.paragraphs.iter().enumerate() {\n"
        "                                for (cc_idx, cc) in cp.controls.iter().enumerate() {\n"
        "                                    if let Control::Footnote(fn_ctrl) = cc {\n"
        "                                        let source = FootnoteSource::TableCell {\n"
        "                                            para_index: para_idx,\n"
        "                                            table_control_index: ctrl_idx,\n"
        "                                            cell_index: cell_idx,\n"
        "                                            cell_para_index: cp_idx,\n"
        "                                            cell_control_index: cc_idx,\n"
        "                                        };\n"
        f"                                        // {TAG} HWPX 단일 단에서 이 쪽 아래에 들어가지 않는 각주(와 그 뒤 각주)는 다음 쪽으로 넘긴다\n"
        "                                        // 높이는 조판한 줄(줄 높이 + 줄 간격)로 재고, 바닥글 자리는 쓰지 않는다(한/글이 본문 아래 끝까지만 둔다)\n"
        "                                        let note_h = composed_footnote_content_height(fn_ctrl, self.dpi);\n"
        "                                        let claude_hwpx_note = st.profile.hwpx_container() && st.col_count == 1;\n"
        "                                        if claude_hwpx_note\n"
        "                                            && (!st.claude_carry_notes.is_empty()\n"
        "                                                || st.current_height + st.projected_footnote_height(note_h, 1)\n"
        "                                                    > st.base_available_height() - st.current_zone_y_offset + 0.5)\n"
        "                                        {\n"
        "                                            st.claude_carry_notes.push((\n"
        "                                                crate::renderer::pagination::FootnoteRef {\n"
        "                                                    number: fn_ctrl.number,\n"
        "                                                    source,\n"
        "                                                    fragment: None,\n"
        "                                                },\n"
        "                                                note_h,\n"
        "                                            ));\n"
        "                                            continue;\n"
        "                                        }\n"
        "                                        if claude_hwpx_note {\n"
        "                                            self.register_unqueued_table_footnote_with_content_height(st, fn_ctrl, source, note_h);\n"
        "                                        } else {\n"
        "                                            self.register_unqueued_table_footnote(st, fn_ctrl, source);\n"
        "                                        }\n"
        "                                    }\n",
    ),
    (
        "renderer/typeset.rs",
        "    fn available_height(&self) -> f64 {\n"
        "        let base = self.base_available_height();\n"
        "        let fn_margin = if self.current_footnote_height > 0.0 {\n",
        "    fn available_height(&self) -> f64 {\n"
        "        let base = self.base_available_height();\n"
        f"        // {TAG} HWPX 는 각주 문단 줄을 불러올 때 만들어(footnote-reflow) 각주 높이를 실제로 잰다. 어림 시절의 안전 여유 40px 는\n"
        "        // 한/글보다 쪽을 일찍 넘긴다(d327: 한/글은 각주 2줄과 구분선을 넣고 0.1px 남기고 마지막 문단을 둔다)\n"
        "        let fn_margin = if self.current_footnote_height > 0.0 && !self.profile.hwpx_container() {\n",
    ),
    (
        "renderer/typeset.rs",
        "        let footnote_penalty = (self.current_footnote_height - self.footer_band_reclaim()).max(0.0);\n",
        f"        // {TAG} HWPX 는 각주가 빈 바닥글 띠를 쓰지 않는다(한/글: 가이드북 2장 두 판 모두 각주 영역이 본문 아래 끝 안에 들고\n"
        "        // 마지막 줄만 약 4px 넘친다). 띠를 빼면 각주 위 본문이 각주와 겹쳤다(2-3 원고 _261012_05 6쪽)\n"
        "        let footnote_penalty = if self.profile.hwpx_container() {\n"
        "            self.current_footnote_height\n"
        "        } else {\n"
        "            (self.current_footnote_height - self.footer_band_reclaim()).max(0.0)\n"
        "        };\n",
    ),
    (
        "renderer/typeset.rs",
        "                            let fn_height = estimate_footnote_note_height(fn_ctrl, self.dpi);\n",
        f"                            // {TAG} HWPX 본문 각주도 조판한 줄(줄 높이 + 줄 간격)로 잰다. 줄 높이만 세면 2줄 각주가 24px(실제 31.2px)로\n"
        "                            // 잡혀 한/글보다 한 줄을 더 담고 각주와 겹쳤다(가이드북 3장 2쪽 각주 6, 7)\n"
        "                            let fn_height = if st.profile.hwpx_container() {\n"
        "                                composed_footnote_content_height(fn_ctrl, self.dpi)\n"
        "                            } else {\n"
        "                                estimate_footnote_note_height(fn_ctrl, self.dpi)\n"
        "                            };\n",
    ),
    (
        "renderer/typeset.rs",
        "                    if break_after_current_table {\n",
        f"                    // {TAG} 각주를 다음 쪽으로 넘겼으면 이 쪽은 찼다. 뒤 흐름은 다음 쪽에서 시작한다(한/글: 표 2-1 캡션이 7쪽 머리)\n"
        "                    if st.profile.hwpx_container() && !st.claude_carry_notes.is_empty() {\n"
        "                        st.advance_column_or_new_page();\n"
        "                    }\n"
        "                    if break_after_current_table {\n",
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
