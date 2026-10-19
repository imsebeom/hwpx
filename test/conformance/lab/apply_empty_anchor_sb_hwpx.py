"""개발용: HWPX 빈 앵커 자리 차지 표(글자처럼 취급 아님)는 다음 항목이 표 앵커여도 호스트 위 간격을 쓰지 않는다.

    python apply_empty_anchor_sb_hwpx.py [--revert]

Task #1147, #1880 은 다음 항목도 표 앵커면 위 간격을 남겼다(HWP 근거). 한/글 새 조판(out/fresh/rt)의 빈 호스트 자리 차지 표 하나짜리 문단
(위 간격 있음) 24건: 다음 문단이 글 19, 표 5 — 모두 「다음 문단 = 호스트 윗변(첫 줄 vpos − 위 간격) + 오프셋 + 바깥 여백 위아래 + 높이」로
위 간격을 뺐다(셈 0건). d302 p66(9x2 표 48746, 위 간격 500, 다음 p67 도 표): 엔진은 위 간격을 더해 표가 본문을 5px 넘어 마지막 행을
다음 쪽으로 가르고 쪽이 하나 늘었다. 한/글은 72749 ≤ 72850 으로 그 쪽에 다 담는다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx empty-anchor-sb-hwpx]"

EDITS = [
    (
        "renderer/typeset.rs",
        "        let before = if !is_tac\n            && table_wrap_take_place\n",
        f"        // {TAG} HWPX 빈 앵커 자리 차지 표는 다음 항목과 상관없이 위 간격을 쓰지 않는다(한/글 새 조판 24/24)\n"
        "        let before = if self.profile.get().hwpx_container() && !is_tac && is_topbottom_empty_anchor {\n"
        "            outer_top\n"
        "        } else if !is_tac\n"
        "            && table_wrap_take_place\n",
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
