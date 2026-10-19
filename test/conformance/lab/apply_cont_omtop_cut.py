"""개발용: HWPX CELL 표가 쪽에 걸쳐 이어지는 조각에서 행 안을 자를 때 바깥 위 여백도 예산에서 뺀다.

    python apply_cont_omtop_cut.py [--revert]

그리기는 이어지는 조각의 쪽 위에 바깥 위 여백을 둔다(partial-omtop-hwpx, 한/글 저장본 d072 쪽마다). 조판의 행 안 자르기 예산은
바깥 아래 여백만 뺐다(cell-split-outer-bottom). 한/글 새 조판 d072 3쪽(표 바깥 여백 283, 칸 여백 141, 줄 1600): 다음 줄 바닥
1043.6 + 칸 아래 여백 1.9 + 바깥 아래 여백 3.8 = 1049.3 > 본문 바닥 1046.9 라 넘기는데, 엔진은 예산 164.0 에 162.7 이 들어간다고 봐
한 줄 더 담았다(쪽 사용 955.3 > 952.4, 뒤 쪽 전체가 한 줄 어긋남). 차이 3.7px = 바깥 위 여백.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx cont-omtop-cut]"

EDITS = [
    (
        "renderer/typeset.rs",
        "            let mut budget =\n"
        "                (avail_for_rows - consumed - cs_before - padding - claude_outer_bottom).max(0.0);\n",
        f"            // {TAG} 이어지는 조각은 쪽 위에 바깥 위 여백을 두고 그린다(partial-omtop-hwpx) — 예산에서도 뺀다(d072 3쪽)\n"
        "            let claude_outer_bottom = claude_outer_bottom\n"
        "                + if claude_outer_bottom > 0.0\n"
        "                    && is_continuation\n"
        "                    // 저장 줄 칸은 그리기가 저장 vpos 대로 이어 그려 새 자르기 자리와 어긋난다(저장 줄 지표 5442 → 5766) — 엔진이 만든 줄만\n"
        "                    && table.cells.iter().all(|c| {\n"
        "                        c.paragraphs.iter().all(crate::renderer::para_has_no_stored_line_segs)\n"
        "                    })\n"
        "                {\n"
        "                    hwpunit_to_px(table.outer_margin_top as i32, self.dpi)\n"
        "                } else {\n"
        "                    0.0\n"
        "                };\n"
        "            let mut budget =\n"
        "                (avail_for_rows - consumed - cs_before - padding - claude_outer_bottom).max(0.0);\n",
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
