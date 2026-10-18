"""개발용: 문단 기준 자리 차지(글앞, 글뒤 포함) 표의 그리기 윗변에 바깥 위 여백을 더한다(HWPX).

    python apply_para_tbl_omtop.py [--revert]

그리기(compute_table_y_position)는 바깥 위 여백을 용지 기준 표에만 더했다(Task #898). d322 1쪽(문단 기준 자리 차지 표, 오프셋 375,
바깥 여백 283): 한/글 PDF 괘선 102.4pt, 엔진 99.6pt — 바깥 위 여백(2.83pt)만큼 위. 조판은 이미 「호스트 윗변 + 오프셋 + 바깥 여백 위아래 +
높이」로 흐름을 센다(exp/harvest_emptyhost_tbl.py 226/253).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx para-tbl-omtop]"

EDITS = [
    (
        "renderer/layout/table_layout.rs",
        "            let om_top_px = if matches!(vert_rel_to, crate::model::shape::VertRelTo::Paper) {\n"
        "                hwpunit_to_px(table.outer_margin_top as i32, self.dpi)\n",
        f"            // {TAG} HWPX 는 문단 기준 표도 가시 윗변 = 기준 + 오프셋 + 바깥 위 여백(d322 1쪽 한/글 PDF 괘선 2.83pt 아래)\n"
        "            let om_top_px = if matches!(vert_rel_to, crate::model::shape::VertRelTo::Paper)\n"
        "                || (self.profile.get().hwpx_container()\n"
        "                    && matches!(vert_rel_to, crate::model::shape::VertRelTo::Para))\n"
        "            {\n"
        "                hwpunit_to_px(table.outer_margin_top as i32, self.dpi)\n",
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
