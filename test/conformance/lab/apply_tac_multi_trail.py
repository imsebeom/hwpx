"""개발용: 글자처럼 취급 표가 여럿 든 문단에서 마지막이 아닌 표 뒤에 줄 간격을 또 더하지 않는다(HWPX).

    python apply_tac_multi_trail.py [--revert]

typeset_tac_table 은 표가 여럿이면 마지막이 아닌 표의 높이를 「줄 높이 + 줄 간격」으로, 마지막 표는 줄 높이만으로 잡는다.
그런데 place_table_with_text 끝의 「TAC 표 trailing line_spacing 복원」은 표마다 줄 간격(total - height_for_fit)을 더해
마지막이 아닌 표에서 줄 간격이 두 번 들어갔다. d159 p134(제목 표 3192 + 큰 표 56208, 줄 간격 452): 한/글 다음 문단 60304,
엔진 60758(+454, 6.0px). 줄 배치를 지운 조판에서 위 간격 판정(fit-sb)과 겹쳐 쪽이 하나 늘었다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx tac-multi-trail]"

EDITS = [
    (
        "renderer/typeset.rs",
        "        let is_tac = self.is_effective_tac_table(para, table, fmt);\n"
        "        if is_tac && fmt.total_height > fmt.height_for_fit && !has_post_text {\n",
        "        let is_tac = self.is_effective_tac_table(para, table, fmt);\n"
        f"        // {TAG} 뒤에 글자처럼 취급 표가 더 있으면 이 표 높이에 줄 간격이 이미 들어 있다(typeset_tac_table 의 is_last_tac)\n"
        "        let claude_later_tac = st.profile.hwpx_container()\n"
        "            && para.controls.iter().skip(ctrl_idx + 1).any(\n"
        "                |c| matches!(c, Control::Table(t) if self.is_effective_tac_table(para, t, fmt)),\n"
        "            );\n"
        "        if is_tac && fmt.total_height > fmt.height_for_fit && !has_post_text && !claude_later_tac {\n",
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
