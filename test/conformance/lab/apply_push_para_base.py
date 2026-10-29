"""개발용: 글 문단이 남은 자리에 안 들어 통째로 새 쪽으로 넘어가면 그 문단의 저장 줄 위치를 새 쪽 기준점으로 잡는다.

    python apply_push_para_base.py [--revert]

근거(2026-10-29 결과보고서 사본): 157번부터 끝까지 저장 줄 위치가 쪽마다 0으로 돌아가지 않고 구역 처음부터 이어진다(간격은 한/글
새 조판과 같다). 173번 「3. [실천과제 3]」이 39쪽에서 안 들어 40쪽으로 넘어가면, 쪽 첫 항목이 정하는 기준점(vpos_page_base)이
비어 있어 다음 문단(174)이 앞 문단 높이로 기준점을 거꾸로 셈하다 줄 간격과 아래 간격(11.7px)을 한 번 더 셌다. 그 쪽이 한/글보다
19.7px 길어져 188번 표가 41쪽으로 밀렸다(한/글은 40쪽, 줄 위치 59971 + 7093 ≤ 본문 67182). 쪽 첫 항목(vpos_snap_current_height)과
같은 규칙으로 기준점을 잡는다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx push-para-base]"

EDITS = [
    (
        "renderer/typeset.rs",
        (
            "            st.advance_column_or_new_page();\n"
            "            // [claude-hwpx restrict-float-defer] 새 쪽 맨 위에 미룬 표부터\n"
            "            if st.profile.hwpx_container()\n"
            "                && !st.deferred_table_controls.is_empty()\n"
            "                && st.current_items.is_empty()\n"
            "            {\n"
            "                self.flush_deferred_table_controls(st, paragraphs, claude_composed, styles, claude_measured, None);\n"
            "            }\n"
        ),
        (
            "            st.advance_column_or_new_page();\n"
            "            // [claude-hwpx restrict-float-defer] 새 쪽 맨 위에 미룬 표부터\n"
            "            if st.profile.hwpx_container()\n"
            "                && !st.deferred_table_controls.is_empty()\n"
            "                && st.current_items.is_empty()\n"
            "            {\n"
            "                self.flush_deferred_table_controls(st, paragraphs, claude_composed, styles, claude_measured, None);\n"
            "            }\n"
            f"            // {TAG} 통째로 넘어온 문단이 새 쪽 첫 항목이면 그 저장 줄 위치가 쪽 기준점이다(쪽 첫 항목 스냅과 같은 규칙).\n"
            "            // 비워 두면 다음 문단이 이 문단 높이로 기준점을 거꾸로 셈해 줄 간격과 아래 간격을 한 번 더 센다(결과보고서 173번)\n"
            "            if st.profile.hwpx_container() && st.col_count == 1 && st.current_items.is_empty() {\n"
            "                if let Some(s0) = para.line_segs.first().filter(|s| !is_synthetic_line_seg(s)) {\n"
            "                    st.vpos_col_anchor = st.current_height;\n"
            "                    st.vpos_page_base = Some(s0.vertical_pos);\n"
            "                    st.vpos_lazy_base = None;\n"
            "                    st.vpos_page_base_stored = true;\n"
            "                    st.vpos_ladder_dirty = false;\n"
            "                }\n"
            "            }\n"
        ),
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
