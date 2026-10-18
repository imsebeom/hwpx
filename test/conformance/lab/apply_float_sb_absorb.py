"""개발용: 자리 차지 개체 아래로 밀린 문단의 위 간격은 개체 아래에 묻는다(HWPX).

    python apply_float_sb_absorb.py [--revert]

정답본 모음(exp/harvest_tbl_nextsb.py): 글이 표보다 짧은 자리 차지 표 호스트 뒤 문단은 vpos 가 표 바닥과 같다 — 위 간격이 표 아래에 묻힌다
(빈 호스트 16, 글 있는 호스트 3, 모두 묻음). 엔진은 문단을 개체 바닥으로 민 뒤(apply_visible_float_exclusions) 위 간격을 또 더했다(d268 p68 +6.7px).
조판에서 이 문단 시작이 개체 바닥으로 밀렸으면 그 문단 위 간격만큼(민 거리 안에서) 되돌린다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx float-sb-absorb]"

EDITS = [
    (
        "renderer/typeset.rs",
        "        st.apply_visible_float_exclusions(exclusion_probe_height);\n",
        f"""        // {TAG} 자리 차지 개체 아래로 밀린 문단의 위 간격은 개체 아래에 묻는다(정답본 19/19)
        let claude_before_float_push = st.current_height;
        st.apply_visible_float_exclusions(exclusion_probe_height);
        if st.profile.hwpx_container() && st.current_height > claude_before_float_push + 0.5 {{
            let pushed = st.current_height - claude_before_float_push;
            st.current_height -= fmt.spacing_before.max(0.0).min(pushed);
        }}
""",
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
