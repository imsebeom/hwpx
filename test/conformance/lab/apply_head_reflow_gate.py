"""개발용: 문단 서식 바꾸기에서 머리(번호, 글머리표) 종류와 수준, 번호 항목이 바뀌어도 줄을 다시 나눈다.

    python apply_head_reflow_gate.py [--revert]

근거: editor/tests/edit_consistency.mjs — set_list(자동 번호) 뒤 편집 직후 조판은 번호 폭 없이 예전 줄 나눔 그대로였고,
같은 결과를 처음부터 조판하면 번호 폭만큼 줄이 달리 꺾였다. 번호 머리 폭은 첫 줄 폭을 줄인다(number-head-line-breaking).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx head-reflow-gate]"

EDITS = [
    (
        "document_core/commands/formatting.rs",
        "        || mods.korean_break_unit.is_some()\n}\n",
        "        || mods.korean_break_unit.is_some()\n"
        f"        // {TAG} 번호, 글머리표 머리는 첫 줄 폭을 줄인다(number-head-line-breaking)\n"
        "        || mods.head_type.is_some()\n"
        "        || mods.para_level.is_some()\n"
        "        || mods.numbering_id.is_some()\n"
        "}\n",
    ),
    (
        "document_core/commands/formatting.rs",
        "            numbering_id: Some(1),\n"
        "            ..Default::default()\n"
        "        };\n"
        "        assert!(!para_shape_mods_affect_text_flow(&mods));\n",
        "            numbering_id: Some(1),\n"
        "            ..Default::default()\n"
        "        };\n"
        "        // [claude-hwpx head-reflow-gate] 번호 머리 폭을 첫 줄에서 빼므로(number-head-line-breaking) 흐름이 바뀐다\n"
        "        assert!(para_shape_mods_affect_text_flow(&mods));\n",
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
