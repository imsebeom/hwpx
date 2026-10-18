"""개발용: 표 속성 바꾸기(캡션 켜고 끄기, 위치, 여백 등) 뒤 표 높이를 다시 재게 dirty 를 켠다.

    python apply_table_props_dirty.py [--revert]

근거: editor/tests/edit_consistency.mjs — table_caption 뒤 편집 직후 조판은 캡션 높이(21px)만큼 뒤 문단을 위로 당겨
p29 를 3쪽에 두고, 같은 결과를 처음부터 조판하면 4쪽에 둔다. 높이 측정기는 dirty 가 꺼진 표의 측정값을 그대로 다시 쓰는데
(height_measurer.rs measure_section_incremental), 캡션을 만드는 경로는 dirty 를 켜지 않았다. 또 글자처럼 취급 표는 표를 담은
줄 높이가 표 높이를 따르는데, 그 줄을 맞추는 sync_tac_table_host_line 은 캡션 표를 건너뛴다. 캡션을 켜거나 끄면 담은 문단을
다시 짜고(reflow_paragraph) 뒤 문단 세로 위치를 잇는다(recalculate_section_vpos).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx table-props-dirty]"

EDITS = [
    (
        "document_core/commands/table_ops.rs",
        "        self.document.sections[section_idx].raw_stream = None;\n"
        "        self.recompose_section(section_idx);\n"
        "        self.paginate_if_needed();\n"
        "\n"
        "        if caption_created {\n",
        f"        // {TAG} 캡션, 바깥 여백, 크기 같은 속성은 표 높이를 바꾼다. dirty 가 꺼져 있으면 측정기가 옛 높이를 다시 쓴다\n"
        "        if let Ok(t) = self.get_table_mut(section_idx, parent_para_idx, control_idx) {\n"
        "            t.dirty = true;\n"
        "        }\n"
        "        // 캡션을 켜거나 끈 글자처럼 취급 표는 표를 담은 줄이 캡션만큼 자라거나 줄어야 한다(sync_tac_table_host_line 은\n"
        "        // 캡션 표를 건너뛴다). 문서를 열 때처럼 그 문단을 다시 짜고 뒤 문단 세로 위치를 잇는다\n"
        "        if (caption_created || caption_changed)\n"
        "            && matches!(\n"
        "                self.document.sections[section_idx].paragraphs[parent_para_idx].controls.get(control_idx),\n"
        "                Some(crate::model::control::Control::Table(t)) if t.common.treat_as_char\n"
        "            )\n"
        "        {\n"
        "            let stored_end = crate::renderer::composer::paragraph_flow_end(\n"
        "                &self.document.sections[section_idx].paragraphs[parent_para_idx],\n"
        "            );\n"
        "            self.reflow_paragraph(section_idx, parent_para_idx);\n"
        "            let hwp3 = self.document.layout_profile().hwp3_layout();\n"
        "            crate::renderer::composer::recalculate_section_vpos(\n"
        "                &mut self.document.sections[section_idx].paragraphs,\n"
        "                parent_para_idx,\n"
        "                None,\n"
        "                stored_end,\n"
        "                &self.styles,\n"
        "                self.dpi,\n"
        "                hwp3,\n"
        "            );\n"
        "        }\n"
        "        self.document.sections[section_idx].raw_stream = None;\n"
        "        self.recompose_section(section_idx);\n"
        "        self.paginate_if_needed();\n"
        "\n"
        "        if caption_created {\n",
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
