"""개발용: HWPX 에서 쪽에 걸쳐 이어지는 자리 차지 표 조각의 위 간격에 바깥 위 여백을 넣는다(조판).

    python apply_cont_omtop_before.py [--revert]

그리기는 이어지는 조각의 쪽 위에 바깥 위 여백을 둔다(partial-omtop-hwpx, 한/글 저장본 d072 쪽마다). 조판의 조각 위 간격
(partial_rowbreak_fragment_spacing_px)은 네이티브 HWP 증거가 있을 때만 이것을 두어, HWPX 는 쪽 위에서 3.8px(여백 283)을 덜 셌다.
한/글 새 조판 d075 6쪽: 이어지는 표 조각 뒤 p16 셋째 줄(바닥 68847 > 본문 68595)을 한/글은 7쪽으로 넘기는데 엔진은 6쪽에 담아
(쪽 사용 923.0 > 914.6) 7쪽 전체가 23.5px 위였다. cont-omtop-cut(행 안 자르기 예산만)을 이 일반판으로 바꾼다 — 행 통째 판정, 행 안
자르기, 조각 높이에 모두 걸린다. 저장 줄 칸은 그리기가 저장 vpos 를 따르므로 표의 칸 줄이 모두 엔진이 만든 줄일 때만.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx cont-omtop-before]"

EDITS = [
    (
        "renderer/typeset.rs",
        "            // [#6143] 오프셋이 쪽 경계에서 이미 소진된 첫 조각은 예산에서도 빼지\n",
        f"            // {TAG} HWPX 이어지는 조각은 쪽 위에 바깥 위 여백을 두고 그린다(partial-omtop-hwpx) — 조판도 센다(d075 6쪽)\n"
        "            let host_before_overhead = if self.profile.get().hwpx_container()\n"
        "                && is_continuation\n"
        "                && host_before_overhead == 0.0\n"
        "                && !table.common.treat_as_char\n"
        "                && is_para_topbottom_float(&table.common)\n"
        "                && matches!(\n"
        "                    table.page_break,\n"
        "                    crate::model::table::TablePageBreak::RowBreak\n"
        "                )\n"
        "                && table.cells.iter().all(|c| {\n"
        "                    c.paragraphs.iter().all(crate::renderer::para_has_no_stored_line_segs)\n"
        "                }) {\n"
        "                hwpunit_to_px(table.outer_margin_top as i32, self.dpi)\n"
        "            } else {\n"
        "                host_before_overhead\n"
        "            };\n"
        "            // [#6143] 오프셋이 쪽 경계에서 이미 소진된 첫 조각은 예산에서도 빼지\n",
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
