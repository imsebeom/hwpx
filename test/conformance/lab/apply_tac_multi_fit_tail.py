"""개발용: 글자처럼 취급 표가 여럿 든(줄이 여럿인) 글 없는 HWPX 문단도 표 줄의 뒤 간격 없이 쪽 끝에 들어가면 둔다.

    python apply_tac_multi_fit_tail.py [--revert]

근거(2026-10-18 정답본 d334 p89): 표 두 개(13x4 61875, 다음 줄 68177)가 든 문단을 한/글은 첫 표를 vpos 6160 에 두어
6160 + 61875 = 68035 <= 본문 68318 로 19쪽에 넣고(줄 간격 660 은 넘침), 둘째 표만 20쪽으로 보낸다. 다중 표 경로
(typeset_tac_table)는 마지막 표가 아니면 줄 높이 + 간격으로 들어감을 따져 첫 표까지 20쪽으로 보내 쪽수가 하나 늘었다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx tac-multi-fit-tail]"

EDITS = [
    (
        "renderer/typeset.rs",
        "        let tac_trailing_spacing_for_fit = if hwpx_rowbreak_tac_missing_owned_line {\n"
        "            (fmt.total_height - fmt.height_for_fit).max(0.0)\n"
        "        } else {\n"
        "            0.0\n"
        "        };\n",
        "        let tac_trailing_spacing_for_fit = if hwpx_rowbreak_tac_missing_owned_line {\n"
        "            (fmt.total_height - fmt.height_for_fit).max(0.0)\n"
        f"        // {TAG} 표가 여럿 든 글 없는 HWPX 문단은 표 줄의 뒤 간격이 쪽 끝을 넘어도 된다(d334 p89: 한/글이 첫 표를 쪽 끝에 둔다)\n"
        "        } else if st.profile.hwpx_container()\n"
        "            && prior_tac + 1 < tac_count\n"
        "            && !para_has_visible_text(para)\n"
        "            && tac_seg_idx < fmt.line_heights.len()\n"
        "        {\n"
        "            -(fmt.line_advance(tac_seg_idx) - fmt.line_heights[tac_seg_idx]).clamp(0.0, table_height)\n"
        "        } else {\n"
        "            0.0\n"
        "        };\n",
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
