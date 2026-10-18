"""개발용: 어울림(Square) 그림만 든 빈 문단의 줄은 HWPX 에서 높이를 센다(Task #901 의 빈 줄 생략을 빈 앵커 문단에는 쓰지 않는다).

    python apply_square_empty_host_line.py [--revert]

근거(2026-10-18 정답본 한/글 줄 기록, harvest_paperfloat.py): 글 없는 본문 문단에 용지, 쪽 기준 개체만 있을 때 다음 문단까지
「줄 높이 + 간격」만큼 내려간다(7건 모두. 어울림 둘 d268 p4, d303, 글 뒤로 둘, 글 앞으로와 자리차지 셋). 엔진은 어울림 그림이 든 문단의
빈칸만 있는 줄을 높이에서 빼(Task #901 wrap guide 줄) d268 p4 가 0 높이가 되어 1쪽이 3840 HWPUNIT 짧았다. 글이 있는 문단의 빈 안내 줄은
종전대로 뺀다. 조판(서식 높이)과 화면 배치(줄 진행)를 같이 고친다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx square-empty-host-line]"

EDITS = [
    (
        "renderer/typeset.rs",
        "                if has_picture_shape_square_wrap && runs_all_whitespace && !line_has_tac_control {\n"
        "                    pairs.push((0.0, 0.0));\n",
        f"                // {TAG} 글 없는 앵커 문단의 줄은 HWPX 에서 센다(d268 p4, d303: 한/글이 줄 높이 + 간격만큼 내려간다)\n"
        "                let claude_empty_host = self.profile.get().hwpx_container() && para.text.trim().is_empty();\n"
        "                if has_picture_shape_square_wrap && runs_all_whitespace && !line_has_tac_control && !claude_empty_host {\n"
        "                    pairs.push((0.0, 0.0));\n",
    ),
    (
        "renderer/layout/paragraph_layout.rs",
        "            let skip_advance_empty_wrap = has_picture_shape_square_wrap\n"
        "                && !has_ole_shape_square_wrap\n"
        "                && runs_all_whitespace\n"
        "                && !line_has_tac_control(composed, line_idx);\n",
        "            let skip_advance_empty_wrap = has_picture_shape_square_wrap\n"
        "                && !has_ole_shape_square_wrap\n"
        "                && runs_all_whitespace\n"
        "                && !line_has_tac_control(composed, line_idx)\n"
        f"                // {TAG} 글 없는 앵커 문단의 줄은 HWPX 에서 진행한다(조판과 같은 판정)\n"
        "                && !(self.profile.get().hwpx_container() && para.is_some_and(|p| p.text.trim().is_empty()));\n",
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
