"""개발용: 1단 구역에서 여러 쪽에 걸쳐 나뉜 표 바로 다음 문단의 단 나누기는 새 쪽을 열지 않는다.

    python apply_colbreak_after_split_table.py [--revert]

근거(2026-10-18 블랙박스 실측, 한/글 2024):
- e36(1단): 단 나누기 문단은 글이든 빈 문단이든 새 쪽을 연다. 다음 문단이 쪽 나눔이면 빈 쪽이 생긴다(엔진과 같음).
- e37(d058 사본 변형): 원본은 2~3쪽에 걸친 40행 표 바로 다음 빈 문단에 단 나누기가 있는데 한/글은 이를 무시하고 3쪽 표 뒤에 둔다(8쪽).
  표를 줄여 한 쪽에 넣으면 단 나누기를 지켜 빈 쪽을 만들고(8쪽, 빈 3쪽), 표와 그 문단 사이에 글 문단을 넣어도 지킨다(9쪽).
엔진은 늘 쪽을 넘겨 d058 이 9쪽이었다. 다단 구역은 실측이 없어 그대로 둔다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx colbreak-after-split-table]"

EDITS = [
    (
        "renderer/typeset.rs",
        "                        self.start_new_column_band(&mut st, para_idx, paragraphs);\n"
        "                    } else {\n"
        "                        st.advance_column_or_new_page();\n"
        "                    }\n",
        "                        self.start_new_column_band(&mut st, para_idx, paragraphs);\n"
        "                    } else if st.col_count == 1\n"
        "                        && matches!(st.current_items.last(), Some(PageItem::PartialTable { para_index, is_continuation: true, .. })\n"
        "                            if *para_index + 1 == para_idx)\n"
        "                    {\n"
        f"                        // {TAG} 여러 쪽에 걸쳐 나뉜 표 바로 다음 문단의 단 나누기는 한/글이 무시한다(e37: d058 변형 셋).\n"
        "                        // 표가 한 쪽에 들어가거나 사이에 다른 문단이 있으면 지킨다(아래 종전 경로)\n"
        "                    } else {\n"
        "                        st.advance_column_or_new_page();\n"
        "                    }\n",
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
