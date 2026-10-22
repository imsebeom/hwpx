"""개발용: 문단을 줄 단위로 나눌 때 각주 안전 여유(40px)를 HWPX 에서 빼지 않는다.

    python apply_split_note_margin.py [--revert]

HWPX 는 각주 문단 줄을 불러올 때 만들어(footnote-reflow) 각주 높이를 실제로 재므로 available_height() 는 이미 이 여유를 쓰지 않는다
(footnote-carry). 줄 나누기 반복문의 첫 쪽 예산만 여유를 따로 빼서, 각주가 있는 쪽에서 한/글보다 한두 줄 일찍 끊었다.
가이드북 파트2 합본 7쪽: 한/글은 「만드는 공간입니다…」 뒤에 두 줄(956.9, 978.3px, 구분선 991.7px)을 더 담는데 엔진은 933px 에서 끊어
8쪽부터 한/글보다 한 쪽씩 늦었다. 10-20 앵커 남은 일 ⓐ(3장 4쪽 한/글 p42 4줄, 엔진 2줄)와 같은 원인.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx split-note-margin]"

EDITS = [
    (
        "renderer/typeset.rs",
        "        while cursor_line < line_count {\n"
        "            let fn_margin = if st.current_footnote_height > 0.0 {\n",
        "        while cursor_line < line_count {\n"
        f"            // {TAG} HWPX 는 각주를 실제 줄로 재므로 안전 여유를 빼지 않는다(available_height 와 같게, 파트2 합본 7쪽)\n"
        "            let fn_margin = if st.current_footnote_height > 0.0 && !st.profile.hwpx_container() {\n",
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
