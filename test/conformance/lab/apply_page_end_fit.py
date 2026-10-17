"""개발용: 쪽 끝에서 마지막 줄이 들어가는지 한/글처럼 판정한다(배치 오차 안전 여유 4px 를 없앤다).

    python apply_page_end_fit.py [--revert]

근거(lab e13): 한 줄 문단을 쪽에 채우고 남은 높이를 바꿔 보면, 한/글은 남은 높이가 줄 높이(줄 간격 제외)를 조금이라도
넘으면 마지막 문단을 그 쪽에 넣는다(10pt: 1000 은 넘김, 1050 은 넣음. 10.5pt: 1050 넘김, 1100 넣음). 엔진은 4px(300 HU)
안전 여유를 빼고 판정해 남은 높이가 줄 높이 + 약 300 은 되어야 넣었다(e13 26경우 중 6경우 다름).
같으면 넘기는 것은 아주 작은 여유(0.01px)로 맞춘다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx page-end-fit]"

EDITS = [
    (
        "renderer/typeset.rs",
        "        const DEFAULT_LAYOUT_DRIFT_SAFETY_PX: f64 = 4.0;\n",
        f"        // {TAG} 한/글에는 이런 여유가 없다 — 남은 높이가 줄 높이를 넘기만 하면 넣는다(같으면 넘김).\n"
        "        // 같을 때 넘기는 몫만 0.01px 로 남긴다(test/conformance/lab e13).\n"
        "        const DEFAULT_LAYOUT_DRIFT_SAFETY_PX: f64 = 0.01;\n",
    ),
]


def main():
    revert = "--revert" in sys.argv
    for rel, find, repl in EDITS:
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
            sys.exit(f"{rel}: 자리 {n}곳 — {find[:50]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel)


if __name__ == "__main__":
    main()
