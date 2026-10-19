"""개발용: 나누지 않음 + flowWithText=0 인 문단 기준 위아래 배치 표는 그릴 때도 흐름 자리에 둔다(쪽 아래로 넘쳐도 끌어올리지 않음).

    python apply_unbounded_float_paint.py [--revert]

조판은 `unbounded-float-table-typeset`(d193 사본 실험)이 이 표를 그 쪽에 넘쳐 두는데, 그리기의 본문 하단 클램프는
「표 전체가 용지 안」일 때만 흐름 자리를 지켜, 용지 밖까지 넘치는 표를 본문 안으로 끌어올려 앞 글을 덮었다
(가이드북 3장 _261019_19 3쪽 그림 3-2: 한/글 표 윗변 792.3px, 아래 1143.4px 로 용지 1122.5 밖, 엔진 678px 로 끌려와 「그림 3-2는」 문단을 덮음).
오프셋 0, 위 정렬일 때만(기존 J3 해제와 같은 형상) 용지 조건을 뺀다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx unbounded-float-paint]"

EDITS = [
    (
        "renderer/layout/table_layout.rs",
        "                            || (signed_hwpunit(table.common.vertical_offset) == 0\n"
        "                                && clamped < y_start - 0.5\n"
        "                                && y_start <= body_bottom + table_height + 0.5\n"
        "                                && y_start + table_height <= page_h_approx + 0.5))\n",
        "                            || (signed_hwpunit(table.common.vertical_offset) == 0\n"
        "                                && clamped < y_start - 0.5\n"
        "                                && y_start <= body_bottom + table_height + 0.5\n"
        f"                                // {TAG} 나누지 않음 + flowWithText=0 표는 한/글이 용지 밖까지 넘쳐 둔다(조판 unbounded-float-table 과 같은 조건)\n"
        "                                && (y_start + table_height <= page_h_approx + 0.5\n"
        "                                    || (self.profile.get().hwpx_container()\n"
        "                                        && !table.common.treat_as_char\n"
        "                                        && !table.common.flow_with_text\n"
        "                                        && matches!(table.page_break, TablePageBreak::None)))))\n",
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
