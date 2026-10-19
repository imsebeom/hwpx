"""개발용: 엔진이 만든 줄(줄 배치 없는 HWPX)도 도형(그림, 묶음 개체) 항목 뒤에는 그리기의 쪽 vpos 기준점을 버리지 않는다.

    python apply_keep_synth_shape.py [--revert]

keep-stored-base 는 저장 줄일 때만 기준점을 둔다. 엔진이 만든 줄에서도 두면(exp/rendery.py --json 으로 문서별 대조):
- 좋아짐: d334 1쪽(글자처럼 취급 도형 줄 3841 + 간격 600 뒤 표가 6pt 위), d034 1쪽 — 쪽 머리 항목이 도형
- 나빠짐: d167 1쪽(−5pt), d201 12쪽, d266 11쪽 — 쪽 머리 항목이 글자처럼 취급 표. 쪽 경로가 앞 문단 끝을 vpos + 줄 높이 + 줄 간격으로만
  세어 그 뒤 쪽에 걸친 표가 앞 문단 아래 간격(500)만큼 위로 그려진다
그래서 엔진이 만든 줄은 도형 항목 뒤에만 기준점을 둔다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx keep-synth-shape]"

EDITS = [
    (
        "renderer/layout.rs",
        "                    .is_some_and(|s| s.tag & crate::model::paragraph::LineSeg::TAG_IMPLEMENTATION_PROPERTY == 0);\n"
        "            if (was_tac",
        f"                    .is_some_and(|s| {{\n"
        f"                        // {TAG} 엔진이 만든 줄도 도형 항목 뒤에는 둔다(d334, d034). 표 항목 뒤는 앞 문단 아래 간격이 빠져 버린다(d167)\n"
        "                        s.tag & crate::model::paragraph::LineSeg::TAG_IMPLEMENTATION_PROPERTY == 0\n"
        "                            || matches!(item, PageItem::Shape { .. })\n"
        "                    });\n"
        "            if (was_tac",
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
