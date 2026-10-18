"""개발용: 한 줄짜리 글자처럼 취급 개체 문단의 「시작이 본문 안이면 담는다」(Task #409 top-fit) 판정에 위 간격을 센다(HWPX).

    python apply_atomic_top_sb.py [--revert]

d268 둘째 구역 p200(글자처럼 취급 묶음 개체 높이 3000, 위 간격 1000): 앞 문단 끝 64865 + 위 간격 1000 = 65865 로 개체 윗변이
본문 끝 65580 아래인데, 엔진은 위 간격을 빼고 시작(864.9 < 874.4px)을 보아 그 쪽에 담았다. 한/글 새 조판(out/fresh)은 다음 쪽 맨 위
(vpos 1000)에 둔다. 개체 윗변은 위 간격 뒤이므로 시작 판정에 위 간격을 더한다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx atomic-top-sb]"

EDITS = [
    (
        "renderer/typeset.rs",
        "        if is_atomic_tac_singleton && st.current_height < available && !st.current_items.is_empty()\n",
        f"        // {TAG} 개체 윗변은 위 간격 뒤다 — 위 간격까지 더해 본문 안인지 본다(d268 둘째 구역 p200, 한/글 새 조판)\n"
        "        let claude_top_sb = if st.profile.hwpx_container() { fmt.spacing_before.max(0.0) } else { 0.0 };\n"
        "        if is_atomic_tac_singleton\n"
        "            && st.current_height + claude_top_sb < available\n"
        "            && !st.current_items.is_empty()\n",
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
