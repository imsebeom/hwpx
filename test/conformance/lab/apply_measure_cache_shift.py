"""개발용: 구역을 다시 짤 때 문단 수가 바뀌었으면 표 높이 측정 캐시를 버린다.

    python apply_measure_cache_shift.py [--revert]

근거: editor/tests/edit_consistency.mjs — create_table, clone_table 뒤 편집 직후 조판은 뒤쪽 표들의 자리가 150px 넘게 어긋났다.
측정기는 dirty 가 꺼진 표의 측정값을 (문단 번호, 컨트롤 번호)로 찾아 다시 쓰는데(height_measurer.rs measure_section_incremental),
표 넣기 경로는 문단 벡터에 바로 문단을 끼우고 번호를 밀지 않아(shift_for_insert 를 거치지 않음) 뒤 표들이 앞 표의 높이를 받았다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx measure-cache-shift]"

EDITS = [
    (
        "document_core/queries/rendering.rs",
        "    pub(crate) fn recompose_section(&mut self, section_idx: usize) {\n"
        "        self.invalidate_page_tree_cache();\n",
        "    pub(crate) fn recompose_section(&mut self, section_idx: usize) {\n"
        "        self.invalidate_page_tree_cache();\n"
        f"        // {TAG} 표 측정 캐시는 (문단 번호, 컨트롤 번호)로 찾는다. 문단을 끼우거나 뺀 뒤 번호를 밀지 않은 경로(표 넣기 등)에서는\n"
        "        // 뒤 표들이 다른 표의 높이를 받으니, 문단 수가 바뀌었으면 버리고 다시 잰다\n"
        "        if let Some(ms) = self.measured_sections.get_mut(section_idx) {\n"
        "            if ms.fallback_paragraphs.len() != self.document.sections[section_idx].paragraphs.len() {\n"
        "                ms.tables.clear();\n"
        "            }\n"
        "        }\n",
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
