"""개발용: HWPX 에서는 한 줄짜리 글자처럼 취급 개체 문단을 쪽 끝에 넘쳐 담지 않는다(Task #409 top-fit 끔).

    python apply_atomic_hwpx_off.py [--revert]

정답본 모음(exp/harvest_atomic_fit.py, 한/글 새 조판): 앞 문단 끝은 본문 안인데 개체 줄을 더하면 넘치는 경우 14건 모두 다음 쪽으로 넘겼고,
줄 바닥이 본문을 넘은 채 그 쪽에 남은 것은 0건이다. 엔진은 시작이 본문 안이면 60px 까지 넘쳐 담아(Task #409, HWP 차트 표본) d333 p4
(글 앞으로 놓은 글자처럼 취급 도형 제목 3683)를 1쪽 바닥에 두었고, 2쪽부터 쪽 전체가 56pt 당겨졌다(문단 쪽 11건).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx atomic-hwpx-off]"

EDITS = [
    (
        "renderer/typeset.rs",
        "        if is_atomic_tac_singleton\n"
        "            && st.current_height + claude_top_sb < available\n",
        f"        // {TAG} HWPX 는 넘쳐 담지 않는다(한/글 새 조판 14/14 다음 쪽, 넘쳐 담음 0)\n"
        "        if is_atomic_tac_singleton\n"
        "            && !st.profile.hwpx_container()\n"
        "            && st.current_height + claude_top_sb < available\n",
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
