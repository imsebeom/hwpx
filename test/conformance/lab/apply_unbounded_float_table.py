"""개발용: 나누지 않음 + flowWithText=0 인 문단 기준 위아래 배치 표는 남은 자리에 안 들어가도 그 쪽에 둔다(아래로 넘친다).

    python apply_unbounded_float_table.py [--revert]

근거(2026-10-18 한/글 2024 블랙박스 실험, d193 사본. scratchpad make_push.py, make_attr.py):
- 원본 d193 p57 표(2x1, 그림 칸, 높이 19501, pageBreak=NONE, flowWithText=0, 문단 기준, 위아래 배치)는 6쪽 바닥(본문 끝 1028px)을 넘어
  856~1073px 에 그대로 그린다. 앞에 빈 문단을 1~4개 넣어 더 밀어도(표 바닥 1159px, 용지 1122px 밖) 6쪽에 둔다.
- 같은 표의 가로 기준만 COLUMN 으로 바꾸면 그대로(6쪽), flowWithText=1 로 바꾸면 7쪽 맨 위로 넘긴다. 나눔을 CELL, TABLE 로 바꿔도
  넘긴다(첫 행 그림이 안 들어가 통째로).
- 정답본 집계(harvest_overflowtbl.py): 남은 자리를 넘는 나누지 않음 표 가운데 flowWithText=0 은 d193 하나이고 넘쳐 둔다.
엔진은 이 표를 7쪽으로 넘겨 d193 이 10쪽이었다(한/글 9쪽).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx unbounded-float-table]"

EDITS = [
    (
        "renderer/typeset.rs",
        "        if st.current_height + whole_fit_table_total <= available\n"
        "            || fits_after_overlay_shapes\n",
        f"        // {TAG} 나누지 않음 + flowWithText=0 인 문단 기준 위아래 배치 표는 한/글이 다음 쪽으로 넘기지 않고 그 쪽에 넘쳐 둔다\n"
        "        // (d193 p57 실험: 빈 문단으로 용지 밖까지 밀어도 그대로, flowWithText=1 이거나 나눔이 CELL, TABLE 이면 넘긴다)\n"
        "        let claude_unbounded_float = st.profile.hwpx_container()\n"
        "            && !table.common.treat_as_char\n"
        "            && !table.common.flow_with_text\n"
        "            && matches!(table.page_break, crate::model::table::TablePageBreak::None)\n"
        "            && matches!(table.common.text_wrap, TextWrap::TopAndBottom)\n"
        "            && matches!(table.common.vert_rel_to, VertRelTo::Para)\n"
        "            && !st.current_items.is_empty()\n"
        "            && table_total <= st.base_available_height();\n"
        "        if st.current_height + whole_fit_table_total <= available\n"
        "            || claude_unbounded_float\n"
        "            || fits_after_overlay_shapes\n",
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
