"""개발용: 중첩 표가 든 칸의 높이에 위아래 배치(문단 기준) 그림, 도형의 바닥을 넣는다.

    python apply_nested_cell_flow_pic.py [--revert]

근거(2026-10-18 d309 진단, 한/글 PDF 괘선): 7x4 표의 행 3 칸(중첩 표 하나, 마지막 빈 문단에 위아래 배치 그림 16672)은 한/글에서
593.0px 다. 줄 기록 끝 27569 + 그림 16672 + 칸 위아래 여백 282 = 44523 HWPUNIT(593.6px)와 같다. 나머지 행 여섯은 엔진과 0.1px 안에서 같다.
엔진의 칸 높이 측정은 중첩 표가 있는 칸에서 「마지막 줄 끝, 글 높이, 중첩 표 바닥, 둘러싸기 개체 바닥」만 보고 위아래 배치 개체는 빼서
384.7px 로 잡았다. 그래서 한/글은 이 표를 두 쪽에 가르는데 엔진은 한 쪽에 넣어 d309 가 한 쪽 적었다.
저장 줄이 이미 개체 아래로 밀린 칸(줄 vpos 가 앞 문단 끝 + 개체 높이 이상)은 이중 계상이므로 넣지 않는다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx nested-cell-flow-pic]"

EDITS = [
    (
        "renderer/height_measurer.rs",
        "    fn cell_wrap_objects_bottom_height(&self, paragraphs: &[Paragraph]) -> f64 {\n",
        f"    /// {TAG} 칸 안 위아래 배치(문단 기준) 그림, 도형의 바닥 = 그 문단 첫 줄 위치 + 오프셋 + 바깥 여백 + 높이 의 최댓값.\n"
        "    /// 저장 줄이 이미 개체 아래로 밀린 문단(첫 줄 vpos >= 앞 문단 끝 + 개체 흐름 높이)은 줄 사다리가 개체를 품었으니 넣지 않는다.\n"
        "    fn claude_cell_flow_objects_bottom(&self, paragraphs: &[Paragraph]) -> f64 {\n"
        "        let mut prev_extent = 0.0f64;\n"
        "        paragraphs\n"
        "            .iter()\n"
        "            .map(|p| {\n"
        "                let first_vpos = p\n"
        "                    .line_segs\n"
        "                    .first()\n"
        "                    .map(|s| hwpunit_to_px(s.vertical_pos, self.dpi))\n"
        "                    .unwrap_or(prev_extent);\n"
        "                let flow = p\n"
        "                    .controls\n"
        "                    .iter()\n"
        "                    .map(|ctrl| match ctrl {\n"
        "                        Control::Picture(pic) if matches!(pic.common.vert_rel_to, VertRelTo::Para) => {\n"
        "                            self.non_inline_control_flow_height(&pic.common)\n"
        "                        }\n"
        "                        Control::Shape(shape) if matches!(shape.common().vert_rel_to, VertRelTo::Para) => {\n"
        "                            self.non_inline_control_flow_height(shape.common())\n"
        "                        }\n"
        "                        _ => 0.0,\n"
        "                    })\n"
        "                    .fold(0.0f64, f64::max);\n"
        "                let absorbed = flow > 0.0 && prev_extent + flow <= first_vpos + 0.5;\n"
        "                let bottom = if flow > 0.0 && !absorbed { first_vpos + flow } else { 0.0 };\n"
        "                prev_extent = p\n"
        "                    .line_segs\n"
        "                    .iter()\n"
        "                    .map(|s| hwpunit_to_px(s.vertical_pos.saturating_add(s.line_height.max(0)), self.dpi))\n"
        "                    .fold(prev_extent, f64::max);\n"
        "                bottom\n"
        "            })\n"
        "            .fold(0.0f64, f64::max)\n"
        "    }\n"
        "\n"
        "    fn cell_wrap_objects_bottom_height(&self, paragraphs: &[Paragraph]) -> f64 {\n",
    ),
    (
        "renderer/height_measurer.rs",
        "                    hwpunit_to_px(last_seg_end, self.dpi)\n"
        "                        .max(text_height)\n"
        "                        .max(nested_bottom)\n"
        "                        .max(self.cell_wrap_objects_bottom_height(&cell.paragraphs))\n",
        "                    hwpunit_to_px(last_seg_end, self.dpi)\n"
        "                        .max(text_height)\n"
        "                        .max(nested_bottom)\n"
        "                        .max(self.cell_wrap_objects_bottom_height(&cell.paragraphs))\n"
        f"                        // {TAG} 위아래 배치 개체 바닥도(d309 행 3: 그림 16672 를 빼 384.7px, 한/글 593px)\n"
        "                        .max(self.claude_cell_flow_objects_bottom(&cell.paragraphs))\n",
    ),
    (
        "renderer/height_measurer.rs",
        "                    let nested_sum =\n"
        "                        self.unabsorbed_nested_tables_height(&cell.paragraphs, styles, depth);\n"
        "                    text_height + nested_sum\n",
        "                    let nested_sum =\n"
        "                        self.unabsorbed_nested_tables_height(&cell.paragraphs, styles, depth);\n"
        f"                    // {TAG} 줄 배치 없는 칸도 위아래 배치 개체 흐름 높이를 더한다(빈 앵커 문단 줄과는 겹친다)\n"
        "                    text_height + nested_sum + self.measure_non_inline_controls_height(&cell.paragraphs)\n"
        "                        - self.claude_empty_host_overlap(&cell.paragraphs)\n",
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
