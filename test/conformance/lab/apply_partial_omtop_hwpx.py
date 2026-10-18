"""개발용: 쪽에 걸친 문단 기준 자리 차지 표의 바깥 위 여백을 HWPX 저장 줄 배치 문서에도 둔다(첫 조각은 오프셋 0 이어도).

    python apply_partial_omtop_hwpx.py [--revert]

partial-float-outer-top 은 줄 배치 없는 문단(스킬 산출물)에만, 첫 조각은 오프셋이 양수일 때만 바깥 위 여백을 더했다. d072(한/글 저장본,
문단 기준 CELL 표 38행, 오프셋 0, 바깥 여백 283): 표가 걸친 쪽마다 엔진 글줄이 한/글 PDF 보다 2.8pt 위다(exp/rendery.py --stored,
1~4쪽, 8쪽 등). 한/글은 첫 조각과 이어지는 조각 모두 쪽 위에 바깥 위 여백을 둔다. HWPX 면 저장 줄 여부와 오프셋 0 을 따지지 않는다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx partial-omtop-hwpx]"

EDITS = [
    (
        "renderer/layout/table_partial.rs",
        "                crate::model::shape::VertRelTo::Para\n"
        "            )\n"
        "            && vert_off_signed > 0\n"
        "        {\n",
        "                crate::model::shape::VertRelTo::Para\n"
        "            )\n"
        f"            // {TAG} HWPX 는 오프셋 0 인 첫 조각도 바깥 위 여백을 둔다(d072)\n"
        "            && (vert_off_signed > 0 || (self.profile.get().hwpx_container() && vert_off_signed == 0))\n"
        "        {\n",
    ),
    (
        "renderer/layout/table_partial.rs",
        "            let claude_outer_top = if paragraphs\n"
        "                .get(para_index)\n"
        "                .is_some_and(crate::renderer::para_has_no_stored_line_segs)\n"
        "            {\n",
        "            let claude_outer_top = if self.profile.get().hwpx_container()\n"
        "                || paragraphs\n"
        "                    .get(para_index)\n"
        "                    .is_some_and(crate::renderer::para_has_no_stored_line_segs)\n"
        "            {\n",
    ),
    (
        "renderer/layout/table_partial.rs",
        "        } else if is_continuation\n"
        "            && !table.common.treat_as_char\n"
        "            && matches!(table.common.vert_rel_to, crate::model::shape::VertRelTo::Para)\n"
        "            && paragraphs\n"
        "                .get(para_index)\n"
        "                .is_some_and(crate::renderer::para_has_no_stored_line_segs)\n"
        "        {\n",
        "        } else if is_continuation\n"
        "            && !table.common.treat_as_char\n"
        "            && matches!(table.common.vert_rel_to, crate::model::shape::VertRelTo::Para)\n"
        "            && (self.profile.get().hwpx_container()\n"
        "                || paragraphs\n"
        "                    .get(para_index)\n"
        "                    .is_some_and(crate::renderer::para_has_no_stored_line_segs))\n"
        "        {\n",
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
