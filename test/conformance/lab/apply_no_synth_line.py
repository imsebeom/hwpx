"""개발용: 줄 배치 없는 HWPX 의 RowBreak 표 칸에 「가짜 둘째 줄」을 붙이던 보정(append_synthetic_cell_line)을 끈다.

    python apply_no_synth_line.py [--revert]

근거: 이 보정은 칸 높이를 맞추려고 「거의 꽉 찬」 문단에 한/글이 줄을 하나 더 썼다고 어림해 줄을 덧붙인다.
한/글 2024 정답본(다시 저장한 줄 배치)과 맞대면 덧붙인 줄은 한/글 줄과 맞지 않는다(네이티브 채점: 끄면 칸 여러 줄
91.9 → 93.6%, 쪽수와 문단 쪽은 그대로).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx no-synth-cell-line]"

EDITS = [
    (
        "document_core/commands/document.rs",
        "    fn append_synthetic_cell_line(para: &mut Paragraph, capacity_hint: Option<u32>) -> bool {\n",
        "    fn append_synthetic_cell_line(para: &mut Paragraph, capacity_hint: Option<u32>) -> bool {\n"
        f"        // {TAG} 한/글 2024 정답본과 맞대면 덧붙인 줄이 한/글 줄과 맞지 않는다(test/conformance/lab README).\n"
        "        // 칸 높이는 줄 배치를 다시 짠 결과로 맞춘다. 아래 본문은 줄이 하나일 때만 덧붙이므로 여기서 돌려보내면 꺼진다.\n"
        "        let _ = capacity_hint;\n"
        "        if para.line_segs.len() == 1 {\n"
        "            return false;\n"
        "        }\n",
    ),
]


def main():
    revert = "--revert" in sys.argv
    for rel, find, repl in EDITS:
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
            sys.exit(f"{rel}: 자리 {n}곳 — {find[:50]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel)


if __name__ == "__main__":
    main()
