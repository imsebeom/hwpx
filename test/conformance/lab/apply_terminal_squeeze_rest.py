"""개발용: 표를 끝내는 마지막 행의 압축(TERMINAL_ROW_BOTTOM_SQUEEZE)을 HWPX 에서는 남은 자리 상한(100px) 없이 쓴다.

    python apply_terminal_squeeze_rest.py [--revert]

근거(2026-10-18 정답본 d266 11쪽, 한/글 PDF): 서약서 표(CELL, 5행)의 마지막 행은 선언 높이 46194(615.9px), 내용은 23줄
567.5px 다. 한/글은 이 행을 1쪽 남은 자리로 줄여 603.0px 로 그리고 표를 11쪽에 통째로 둔다(엔진이 잰 남은 자리 603.1px).
엔진의 압축 규칙은 「쪽 끝자락(남은 자리 100px 이하)」에서만 켜져 행을 12쪽으로 넘겼고, 뒤 쪽이 모두 밀려 14쪽(한/글 13쪽)이
됐다. 넘침 13px 이하, 내용 여유 12px 이상 조건은 그대로 둔다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx terminal-squeeze-rest]"

EDITS = [
    (
        "renderer/typeset.rs",
        "                    && squeeze_rest <= TERMINAL_ROW_BOTTOM_SQUEEZE_MAX_REST_PX\n",
        f"                    // {TAG} HWPX 는 남은 자리 상한 없이 압축한다(d266 서약서 표: 남은 603px 에 선언 616px 행을 603px 로)\n"
        "                    && (squeeze_rest <= TERMINAL_ROW_BOTTOM_SQUEEZE_MAX_REST_PX\n"
        "                        || st.profile.hwpx_container())\n",
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
