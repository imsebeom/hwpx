"""개발용: HWPX 의 글자처럼 취급 표는 행 수와 flowWithText 에 상관없이 쪽에서 나누지 않는다.

    python apply_tac_no_split.py [--revert]

근거(2026-10-29 결과보고서 사본, 한/글 13.0 재저장본과 PDF): 학년별 수업 표 16개(25~30행, treatAsChar=1, flowWithText=0,
pageBreak=CELL)를 한/글은 하나도 나누지 않는다.
  - 157번(실제 높이 66690)은 앞 쪽에 제목 한 줄(1320)이 있어 남은 자리 65862 에 안 들어가자 통째로 다음 쪽 맨 위로 넘긴다.
  - 163번(71101), 166번(69305)은 본문 높이 67182 보다 커도 쪽 맨 위에 통째로 두고 꼬리말 자리(쪽 번호)까지 넘쳐 그린다.
정답본 새 조판 327개에서도 쪽 끝을 넘는 글자처럼 취급 표 11건(모두 flowWithText=1) 모두 쪽 맨 위에 통째로 있고 다음 문단이
새 쪽에서 시작한다. 엔진은 Task #991 이 1행 표만 통째로 넘기고, flowWithText=0 표를 블록 표로 다뤄 행에서 잘랐다
(oversized-tac-table 은 선언 높이로만 판정해, 선언 높이가 낡아 본문보다 작은 이 문서에서는 걸리지 않았다). 54쪽 → 한/글 49쪽.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx tac-no-split]"

EDITS = [
    (
        "renderer/typeset.rs",
        "        if table.common.treat_as_char && table.row_count <= 1 && table_total <= available {\n",
        (
            f"        // {TAG} HWPX 는 여러 행 표도, 쪽보다 큰 표도 나누지 않는다. 남은 자리에 안 들면 다음 쪽 맨 위에 통째로,\n"
            "        // 쪽 맨 위에서도 안 들면 그대로 두고 아래로 넘친다(결과보고서 사본 157, 163, 166번 표, 정답본 11건)\n"
            "        let claude_tac_no_split = st.profile.hwpx_container() && table.common.treat_as_char;\n"
            "        if claude_tac_no_split\n"
            "            || (table.common.treat_as_char && table.row_count <= 1 && table_total <= available)\n"
            "        {\n"
        ),
    ),
    (
        "renderer/typeset.rs",
        (
            "            || (table.common.treat_as_char && table.row_count <= 1 && table_total <= available)\n"
            "        {\n"
            "            if !st.current_items.is_empty() {\n"
            "                st.advance_column_or_new_page();\n"
            "            }\n"
        ),
        (
            "            || (table.common.treat_as_char && table.row_count <= 1 && table_total <= available)\n"
            "        {\n"
            f"            // {TAG} 한 줄짜리 표 문단의 줄 뒤 간격은 쪽 끝을 넘어도 된다(tac-multi-fit-tail 과 같은 한/글 규칙). 결과보고서 21:11 판\n"
            "            // 157번 표: 제목 뒤 1670 + 표 65456 = 67126 ≤ 본문 67182 라 한/글은 같은 쪽에 두는데, 간격 720 까지 세면 넘쳤다\n"
            "            // 높이는 한/글이 저장한 표 줄(엔진이 만든 줄이 아닐 때)을 먼저 쓴다 — 엔진 행 측정이 한/글보다 클 때가 있다(157번: 879.4px 대 줄 872.7px)\n"
            "            let claude_tac_h = match para.line_segs.as_slice() {\n"
            "                [seg] if !is_synthetic_line_seg(seg) && seg.line_height > 0 => hwpunit_to_px(seg.line_height, self.dpi),\n"
            "                _ => ft.effective_height,\n"
            "            };\n"
            "            let claude_fits_without_tail = claude_tac_no_split\n"
            "                && st.current_height + ft.host_spacing.before + claude_tac_h <= available + 0.5;\n"
            "            if !st.current_items.is_empty() && !claude_fits_without_tail {\n"
            "                st.advance_column_or_new_page();\n"
            "            }\n"
        ),
    ),
    (
        "renderer/typeset.rs",
        (
            "            && st.current_height + declared_object_total <= available\n            && !hwpx_tac_cell_leftover_missing_owned_line;\n"
        ),
        (
            "            && st.current_height + declared_object_total <= available\n"
            "            && !hwpx_tac_cell_leftover_missing_owned_line\n"
            f"            // {TAG} 한/글이 저장한 표 줄이 선언 높이보다 크면 선언이 낡은 것이다(157번 표: 선언 62047, 줄 66690 —\n"
            "            // 한/글은 줄 높이로 재 다음 쪽으로 넘긴다). 그때는 선언 높이로 남은 자리에 넣지 않는다\n"
            "            && !(st.profile.hwpx_container()\n"
            "                && para.line_segs.len() == 1\n"
            "                && para.line_segs.first().is_some_and(|seg| {\n"
            "                    !is_synthetic_line_seg(seg)\n"
            "                        && seg.line_height\n"
            "                            > table.common.height.min(i32::MAX as u32) as i32\n"
            "                                + i32::from(table.outer_margin_top)\n"
            "                                + i32::from(table.outer_margin_bottom)\n"
            "                                + 75\n"
            "                }));\n"
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
