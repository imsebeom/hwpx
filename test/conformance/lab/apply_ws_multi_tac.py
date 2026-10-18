"""개발용: 빈칸만 든 문단에 글자처럼 취급 표가 둘 이상이면 글 없는 문단처럼 개체 폭으로 줄을 나눈다.

    python apply_ws_multi_tac.py [--revert]

근거(2026-10-18 정답본 d159 p0): run 이 [표 1(폭 47913)][빈칸 둘][표 2(폭 47908)][빈칸 둘] 이고 줄 폭은 48188 이다. 한/글은 두 줄로 놓는다
(줄 1 높이 6515 = 표 1, 줄 2 는 textpos 34 = 표 2 자리에서 시작, 높이 9835 = 표 2). 엔진 줄 나눔은 글자처럼 취급 표의 폭을 세지 않고
(flow_inline_controls 가 표를 뺀다) 표 하나짜리만 「제 줄 차지」 규칙으로 따로 다뤄, 이 문단을 한 줄에 겹쳤다. 그래서 1쪽 표지가
8115 HWPUNIT 짧아져 다음 쪽 첫 표까지 1쪽에 담겼다(한/글 15쪽, 엔진 14쪽). 글이 아예 없는 문단은 이미 개체 폭으로 줄을 나누니
같은 경로를 쓰고, 줄 시작은 개체의 원래 UTF-16 위치(control_utf16_positions, 빈칸 포함)로 적는다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx ws-multi-tac]"

EDITS = [
    (
        "renderer/composer/line_breaking.rs",
        "    if para.text.is_empty() {\n"
        "        // [#4677] 각 인라인 개체의 **UTF-16 오프셋**을 함께 들고 다닌다. lineseg 의\n",
        f"    // {TAG} 빈칸만 든 문단에 글자처럼 취급 표가 둘 이상이면 글 없는 문단처럼 개체 폭으로 줄을 나눈다\n"
        "    // (d159 p0: 한/글은 줄 폭에 가까운 표 둘을 두 줄로 놓는데 엔진 줄 나눔은 표 폭을 세지 않아 한 줄에 겹쳤다)\n"
        "    let claude_ws_tac = !para.text.is_empty()\n"
        "        && para.text.chars().all(char::is_whitespace)\n"
        "        && para\n"
        "            .controls\n"
        "            .iter()\n"
        "            .filter(|c| matches!(c, Control::Table(t) if t.common.treat_as_char))\n"
        "            .count()\n"
        "            >= 2;\n"
        "    if para.text.is_empty() || claude_ws_tac {\n"
        "        // [#4677] 각 인라인 개체의 **UTF-16 오프셋**을 함께 들고 다닌다. lineseg 의\n",
    ),
    (
        "renderer/composer/line_breaking.rs",
        "            .scan(0u32, |utf16_pos, ctrl| {\n"
        "                let start = *utf16_pos;\n"
        "                if ctrl.occupies_ctrl_char_slot() {\n"
        "                    *utf16_pos += CTRL_CHAR_CODE_UNITS;\n"
        "                }\n"
        "                Some((start, ctrl))\n"
        "            })\n"
        "            .filter_map(|(start, ctrl)| inline_control_size_hwp(ctrl).map(|size| (start, size)))\n",
        "            .scan(0u32, |utf16_pos, ctrl| {\n"
        "                let start = *utf16_pos;\n"
        "                if ctrl.occupies_ctrl_char_slot() {\n"
        "                    *utf16_pos += CTRL_CHAR_CODE_UNITS;\n"
        "                }\n"
        "                Some((start, ctrl))\n"
        "            })\n"
        f"            // {TAG} 빈칸이 섞이면 개체 위치를 원래 스트림 위치로(빈칸 몫 포함)\n"
        "            .zip(claude_ws_tac.then(|| para.control_utf16_positions()).unwrap_or_default().into_iter().map(Some).chain(std::iter::repeat(None)))\n"
        "            .map(|((start, ctrl), raw)| (raw.unwrap_or(start), ctrl))\n"
        "            .filter_map(|(start, ctrl)| inline_control_size_hwp(ctrl).map(|size| (start, size)))\n",
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
