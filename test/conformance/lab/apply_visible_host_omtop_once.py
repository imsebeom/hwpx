"""개발용: HWPX 에서 글 있는 문단의 자리 차지 표(문단 기준)가 바깥 위 여백을 두 번 더해 그만큼 아래에 그려지던 것을 고친다.

    python apply_visible_host_omtop_once.py [--revert]

para-tbl-omtop 이 compute_table_y_position 에서 HWPX 문단 기준 표의 윗변에 바깥 위 여백을 더하는데, 글 있는 호스트 경로는
기준 y 를 넘길 때 이미 `para_y + 바깥 위 여백` 을 준다. 한/글 새 조판 d027 p3(오프셋 2362, 여백 283): 표 위 괘선 265.1px,
엔진 269.2px(+3.8). d102 p93(오프셋 4256, 여백 283)도 칸 글이 +3.7px. HWPX 에서는 기준 y 에 여백을 넣지 않는다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx visible-host-omtop-once]"

EDITS = [
    (
        "renderer/layout.rs",
        "                        Some(para_y_for_table + visible_outer_top_px),\n",
        f"                        // {TAG} HWPX 는 compute_table_y_position 이 바깥 위 여백을 더한다(para-tbl-omtop)\n"
        "                        Some(\n"
        "                            para_y_for_table\n"
        "                                + if self.profile.get().hwpx_container() {\n"
        "                                    0.0\n"
        "                                } else {\n"
        "                                    visible_outer_top_px\n"
        "                                },\n"
        "                        ),\n",
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
