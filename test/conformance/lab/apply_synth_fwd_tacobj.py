"""개발용: 앞 문단이 글 없이 글자처럼 취급 개체(도형, 그림)만 든 줄이면 합성 줄이어도 vpos 로 앞으로 맞춘다.

    python apply_synth_fwd_tacobj.py [--revert]

그리기는 그런 줄을 「높이 0 + 줄 간격」으로 지나고 개체 높이는 도형 항목이 따로 그린다. 저장 줄 문서는 다음 문단을 vpos 로 맞춰 바로잡히지만,
엔진이 만든 줄은 #1811 이 48px 이하 앞으로 맞추기를 막아 순차 y 에 남는다. d333 1쪽: p0(글 앞으로 놓은 글자처럼 취급 사각형 3683, 줄 간격 1920)
뒤 p1 이 162.5px(한/글과 저장 줄 188.1px) — 19.2pt 위.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx synth-fwd-tacobj]"

EDITS = [
    (
        "renderer/height_cursor.rs",
        "        if synthetic_prev_seg\n"
        "            && result > y_offset + 0.5\n"
        "            && result - y_offset <= SYNTH_FORWARD_REANCHOR_MIN_PX\n"
        "        {\n",
        f"        // {TAG} 앞 문단이 글 없이 글자처럼 취급 개체만 든 줄이면 순차 y 가 그 줄 높이를 빠뜨린다 — 막지 않는다(d333 p0)\n"
        "        let claude_prev_tac_object_line = !para_has_visible_text(prev_para)\n"
        "            && prev_para.controls.iter().any(|c| match c {\n"
        "                Control::Shape(s) => s.common().treat_as_char,\n"
        "                Control::Picture(p) => p.common.treat_as_char,\n"
        "                _ => false,\n"
        "            });\n"
        "        if synthetic_prev_seg\n"
        "            && !claude_prev_tac_object_line\n"
        "            && result > y_offset + 0.5\n"
        "            && result - y_offset <= SYNTH_FORWARD_REANCHOR_MIN_PX\n"
        "        {\n",
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
