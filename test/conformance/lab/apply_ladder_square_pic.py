"""개발용: tac-row-ladder 의 칸 안 개체 바닥(ladder-pic-bottom)에 어울림(SQUARE) 그림, 도형도 넣는다. ladder-pic-bottom 다음에 적용한다.

    python apply_ladder_square_pic.py [--revert]

근거(회귀 모음 「협력적 수업설계 직무연수 운영계획」 c41, 15번 문단 1×1 글자처럼 취급 표): 칸 첫 문단에 어울림 그림(문단 기준, 위치 315,
높이 13351)이 있고 글이 그 옆으로 흐른다. 한/글 표 높이 13948 = 그림 바닥 13666 + 칸 여백 282. 사다리가 위아래 배치만 보고 어울림 그림을
빼 표를 글 높이(12896)로 쟀고, 열 때 다시 재기가 그 값을 적어 12쪽부터 글이 40px 위로 올라갔다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx ladder-square-pic]"

EDITS = [
    (
        "renderer/height_measurer.rs",
        (
            "                            if common.treat_as_char\n"
            "                                || !matches!(common.text_wrap, TextWrap::TopAndBottom)\n"
            "                                || !matches!(common.vert_rel_to, VertRelTo::Para)\n"
        ),
        (
            f"                            // {TAG} 어울림 그림, 도형도 칸을 그 바닥까지 키운다(c41 15번 표: 한/글 13948 = 그림 바닥 13666 + 여백)\n"
            "                            let claude_wrap_ok = matches!(common.text_wrap, TextWrap::TopAndBottom)\n"
            "                                || (matches!(common.text_wrap, TextWrap::Square) && !matches!(ctl, Control::Table(_)));\n"
            "                            if common.treat_as_char\n"
            "                                || !claude_wrap_ok\n"
            "                                || !matches!(common.vert_rel_to, VertRelTo::Para)\n"
        ),
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
