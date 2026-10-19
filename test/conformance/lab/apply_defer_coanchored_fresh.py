"""개발용: HWPX 에서 한 문단의 뒤쪽 공동 앵커 자리 차지 표가 남은 자리에 안 들어가고 새 쪽에는 들어가면 미루고, 뒤 글은 지금 쪽을 채운다.

    python apply_defer_coanchored_fresh.py [--revert]

한/글 새 조판 d322 p77(빈 문단에 문단 기준 자리 차지 CELL 표 둘, 오프셋 같음): 32쪽 = 실과과 표 + 호스트 줄 + p78, 33쪽 = 체육과 표 혼자.
사본 실험(exp/make_twofloat.py): p78 을 글 40개로 바꾸면 01~11 은 32쪽, 33쪽 체육과 표 혼자, 12~40 은 34쪽. 엔진은 체육과 표를 33쪽에 놓은 뒤
p78 을 34쪽에 두어 쪽이 하나 늘었다.
- 미루기: 블록 표를 놓기 전, 같은 문단에서 앞서 놓인 표가 있고(order_pos > 0) 공동 앵커 표이며 표 높이가 남은 자리보다 크고 새 쪽에는 들어가면
  deferred_table_controls 에 넣고 건너뛴다.
- 꺼내기: 문단을 처리하기 전, 미룬 표가 있고 쪽이 비었거나 이 문단이 쪽 나누기거나 첫 줄(위 간격 포함)이 남은 자리에 안 들어가면
  (먼저 쪽을 넘긴 뒤) 미룬 표를 새 쪽 맨 위에 놓는다. 실험 순서(32쪽 글, 33쪽 체육과 표, 34쪽 글)가 한/글과 같아졌다.
  남은 차이: 첫 표 뒤 빈 호스트 줄을 엔진이 높이에 넣지 않아 32쪽에 글이 한 줄 더 들어간다(엔진 12줄, 한/글 11줄).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx defer-coanchored-fresh]"

EDITS = [
    (
        "renderer/typeset.rs",
        '            if std::env::var("RHWP_FLOW_DBG").is_ok() {\n',
        f"            // {TAG} 미룬 공동 앵커 표는 새 쪽 맨 위에 놓는다 — 쪽이 비었거나 이 문단이 쪽 나누기면(먼저 넘긴 뒤)\n"
        "            if st.profile.hwpx_container() && !st.deferred_table_controls.is_empty() {\n"
        "                let claude_forced_break = matches!(\n"
        "                    para.column_type,\n"
        "                    ColumnBreakType::Page | ColumnBreakType::Section\n"
        "                );\n"
        "                // 첫 줄(위 간격 포함)이 남은 자리에 안 들어가도 새 쪽을 열고 미룬 표부터 놓는다(사본 실험: 글 12 보다 체육과 표가 먼저)\n"
        "                let claude_first_need = para\n"
        "                    .line_segs\n"
        "                    .first()\n"
        "                    .map(|s| hwpunit_to_px(s.line_height, self.dpi))\n"
        "                    .unwrap_or(0.0)\n"
        "                    + styles\n"
        "                        .para_styles\n"
        "                        .get(para.para_shape_id as usize)\n"
        "                        .map(|ps| ps.spacing_before.max(0.0))\n"
        "                        .unwrap_or(0.0);\n"
        "                let claude_first_overflows =\n"
        "                    st.current_height + claude_first_need > st.available_height() + 0.01;\n"
        "                if (claude_forced_break || claude_first_overflows) && !st.current_items.is_empty() {\n"
        "                    st.advance_column_or_new_page();\n"
        "                }\n"
        "                if st.current_items.is_empty() {\n"
        "                    self.flush_deferred_table_controls(\n"
        "                        &mut st,\n"
        "                        paragraphs,\n"
        "                        composed,\n"
        "                        styles,\n"
        "                        measured_tables,\n"
        "                        None,\n"
        "                    );\n"
        "                }\n"
        "            }\n"
        '            if std::env::var("RHWP_FLOW_DBG").is_ok() {\n',
    ),
    (
        "renderer/typeset.rs",
        "                        let pages_before_block_table = st.pages.len();\n",
        f"                        // {TAG} 같은 문단 뒤쪽 공동 앵커 표가 남은 자리에 안 들어가고 새 쪽에는 들어가면 미룬다(d322 p77 체육과 표)\n"
        "                        if st.profile.hwpx_container()\n"
        "                            && st.col_count == 1\n"
        "                            && order_pos > 0\n"
        "                            && !st.current_items.is_empty()\n"
        "                            && self.is_deferred_coanchored_rowbreak_table(para, table, &fmt)\n"
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
        "                            continue;\n"
        "                        }\n"
        "                        let pages_before_block_table = st.pages.len();\n",
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
