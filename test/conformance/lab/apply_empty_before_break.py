"""개발용: 순수 HWPX 에서 쪽 나눔 문단 바로 앞 빈 문단이 현재 쪽에 안 들어가면 흡수하지 않고 다음 쪽으로 넘긴다.

    python apply_empty_before_break.py [--revert]

근거(2026-10-18, 한/글 2024 저장 정답본): 쪽 나눔(pageBreak=1) 문단 바로 앞 빈 문단 205개 중 194개는 그냥 들어가고,
안 들어가는 11개 중 9개는 다음 쪽 첫머리로 넘어가(다음 문단의 쪽 나눔으로 빈 쪽이 생김) 1개만 쪽 아래로 흡수됐다
(harvest_emptybreak.py). d078(채움AI 문항) 은 1쪽 표 뒤 빈 문단이 2쪽으로 넘어가 한/글 7쪽, 엔진은 흡수해 6쪽이었다.
엔진의 흡수 분기(Task #967)는 HWP5 표본(sample18.hwp)에서 나온 규칙이라 HWP5 출처(hwp5_stored_pagination_layout)에만 남긴다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx empty-before-break]"

EDITS = [
    (
        "renderer/typeset.rs",
        "                    let avail = st.available_height() - st.current_height;\n"
        "                    if empty_h_px > avail {\n"
        "                        // [#1706] 빈 paragraph 가 fit 안 됨.\n",
        "                    let avail = st.available_height() - st.current_height;\n"
        f"                    // {TAG} 순수 HWPX(한/글 2024 저장본)는 안 들어가는 빈 문단을 다음 쪽으로 넘긴다(정답본 11곳 중 9곳, d078).\n"
        "                    // 아래 흡수는 HWP5 표본(sample18) 규칙이라 HWP5 출처에만 둔다\n"
        "                    let claude_pure_hwpx = st.profile.hwpx_container() && !st.profile.hwp5_stored_pagination_layout();\n"
        "                    if empty_h_px > avail && !claude_pure_hwpx {\n"
        "                        // [#1706] 빈 paragraph 가 fit 안 됨.\n",
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
