"""개발용: 쪽에 걸칠 표는 칸 안 각주 높이를 시작 쪽에서 미리 빼지 않는다(HWPX 단일 단).

    python apply_cellnote_split_end.py [--revert]

한/글 사본 실험(exp/make_cellnote_split.py, 가이드북 파트2 합본 「API」 상자 표의 칸 문단 수를 바꾼 13개): 칸 안 각주는 표지가
첫 쪽에 있어도 표가 끝나는 쪽 아래에 놓이고(13/13), 시작 쪽과 중간 쪽 표는 본문 끝까지 찬다(첫 쪽 상자 바닥 1008px).
끝나는 쪽에 자리가 없으면 표를 줄이지 않고 각주를 다음 쪽으로 넘긴다(n72). 엔진은 표 전체 각주를 시작 쪽에서 미리 빼
첫 조각을 일찍 잘랐고, 그만큼 끝나는 쪽이 길어져 각주가 다음 쪽(다른 표가 꽉 찬 쪽)으로 밀려 겹쳤다(합본 117~119쪽).
끝나는 쪽 등록과 넘기기는 이미 한/글과 같다(footnote-carry).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx cellnote-split-end]"

EDITS = [
    (
        "renderer/typeset.rs",
        "        let mut fn_margin = if total_footnote > 0.0 {\n"
        "            if next_starts_new_page\n"
        "                || internal_reset_tail_uses_actual_footnote_boundary\n",
        f"        // {TAG} 한/글은 쪽에 걸친 표의 칸 각주를 표가 끝나는 쪽에 둔다 — 이 쪽에 표 전체가 안 들어가면(조각으로 나뉘면)\n"
        "        // 칸 각주를 미리 빼지 않는다(사본 실험 13/13, 가이드북 파트2 합본 117쪽)\n"
        "        if st.profile.hwpx_container()\n"
        "            && st.col_count == 1\n"
        "            && !table.common.treat_as_char\n"
        "            && ft.table_footnote_count > 0\n"
        "            && st.current_height + table_total\n"
        "                > st.base_available_height() - st.projected_footnote_height(0.0, 0) - st.current_zone_y_offset + 0.5\n"
        "        {\n"
        "            total_footnote = st.projected_footnote_height(0.0, 0);\n"
        "        }\n"
        "        let mut fn_margin = if total_footnote > 0.0 {\n"
        "            if next_starts_new_page\n"
        "                || internal_reset_tail_uses_actual_footnote_boundary\n",
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
