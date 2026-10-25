"""개발용: 「셀 단위로 나눔」 표 칸 안의 「셀 단위로 나눔」 1×1 중첩 표는 한 쪽보다 작아도 쪽 끝에서 나눈다.

    python apply_cell_nested_split.py [--revert]

근거(사본 실험, 한국문화 1단원 삽입본 「푸른 바다로 둘러싸여 있어요」 상자, scratchpad mkvar.py → 한/글 2024 PDF):
바깥 1×1 표(CELL) 칸에 글 세 줄과 1×1 중첩 표(그림 문단, 빈 문단 셋, 글 세 줄)가 있다.
  - 바깥 CELL, 안 CELL: 한/글은 안 표를 쪽 끝에서 나눈다(그림과 「동해」 줄은 앞 쪽, 「서해」부터 다음 쪽)
  - 바깥 CELL, 안 TABLE/NONE: 안 표를 통째로 다음 쪽으로(엔진도 같다)
  - 바깥 TABLE: 바깥 표를 통째로 다음 쪽으로(엔진은 나눈다 — 이 패치 밖)
  - 한/글 PDF 의 그림 바닥(695.4pt)과 「동해」 줄 위(749.4pt) 사이 54pt = 그림 줄 간격 6pt + 빈 문단 셋 x (10pt + 6pt)
HWPX pageBreak="CELL" 은 모델 RowBreak 다.
고친 것:
  ① 1×1 자식 조각 게이트에 「바깥과 자식 모두 RowBreak」를 더한다. 이때 조각은 자식 칸의 canonical CellUnit 으로 잰다
     (legacy 조각은 빈 문단을 줄 간격 없이 13.33px 로 재고, 그리기는 CellUnit 으로 재서 컷이 어긋났다)
  ② 1×1 RowBreak 칸의 빈 문단 접기에서 줄 배치 없는 HWPX 빈 문단은 뺀다(한/글은 한 줄로 조판한다)
  ③ 나눈 조각을 그릴 때 앞 문단에 줄 배치가 없으면, 흐름보다 위로 되돌아가는 저장 vpos 는 낡은 값이라 쓰지 않는다
SRC 는 스킬 빌드 소스(~/.claude/skills/hwpx/editor/.build/rhwp/src)다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx cell-nested-split]"
F = "renderer/layout/table_layout.rs"

EDITS = [
    (
        F,
        "                    let frags = self.nested_table_mixed_fragment_heights(nt, styles);\n",
        (
            f"                    // {TAG} 바깥 표와 자식 표가 모두 「셀 단위로 나눔」(HWPX CELL, 모델 RowBreak)이면\n"
            "                    // 한/글은 한 쪽보다 작은 1×1 자식 표도 쪽 끝에서 나눈다(한국문화 1단원 사본 실험).\n"
            "                    // 그 조각은 그리기와 같은 자식 칸 CellUnit 으로 잰다\n"
            "                    let cell_split_child = self.profile.get().hwpx_container()\n"
            "                        && matches!(table.page_break, TablePageBreak::RowBreak)\n"
            "                        && matches!(nt.page_break, TablePageBreak::RowBreak)\n"
            "                        && !table.common.treat_as_char\n"
            "                        && !nt.common.treat_as_char;\n"
            "                    let frags = cell_split_child\n"
            "                        .then(|| self.claude_child_cell_unit_fragments(nt, styles))\n"
            "                        .flatten()\n"
            "                        .unwrap_or_else(|| self.nested_table_mixed_fragment_heights(nt, styles));\n"
        ),
    ),
    (
        F,
        (
            "                    if frags.len() > 1\n"
            "                        && (total_frag_h > multi_page_px\n"
            "                            || exceeds_physical_page\n"
            "                            || native_short_parent_child_fragment\n"
            "                            || stored_frame_tail_before_next_para)\n"
        ),
        (
            "                    if frags.len() > 1\n"
            "                        && (total_frag_h > multi_page_px\n"
            "                            || exceeds_physical_page\n"
            "                            || native_short_parent_child_fragment\n"
            "                            || stored_frame_tail_before_next_para\n"
            "                            || cell_split_child)\n"
        ),
    ),
    (
        F,
        "    fn nested_table_mixed_fragment_heights(\n",
        (
            f"    /// {TAG} 1×1 자식 표 칸의 CellUnit 을 부모 조각으로 옮긴다(direct HWPX 투영과 같은 꼴, 재귀 아님).\n"
            "    fn claude_child_cell_unit_fragments(\n"
            "        &self,\n"
            "        table: &crate::model::table::Table,\n"
            "        styles: &ResolvedStyleSet,\n"
            "    ) -> Option<Vec<NestedFlowFragment>> {\n"
            "        if table.row_count != 1 {\n"
            "            return None;\n"
            "        }\n"
            "        let mut cells = table.cells.iter().filter(|cell| cell.row == 0 && cell.row_span == 1);\n"
            "        let (Some(cell), None) = (cells.next(), cells.next()) else {\n"
            "            return None;\n"
            "        };\n"
            "        let units = self.cell_units(cell, table, styles);\n"
            "        Some(\n"
            "            units\n"
            "                .iter()\n"
            "                .map(|unit| {\n"
            "                    let visible = Self::cell_unit_has_visible_content(cell, unit);\n"
            "                    NestedFlowFragment {\n"
            "                        height: unit.height,\n"
            "                        hard_break_before: false,\n"
            "                        stored_frame_break_before: false,\n"
            "                        trailing: unit.mixed_nested_trailing || !visible,\n"
            "                        content_height: if unit.mixed_nested_content_height > 0.0 {\n"
            "                            unit.mixed_nested_content_height\n"
            "                        } else if visible {\n"
            "                            unit.height\n"
            "                        } else {\n"
            "                            0.0\n"
            "                        },\n"
            "                        recursive: false,\n"
            "                        starts_after_table: unit.mixed_nested_starts_after_table,\n"
            "                        source_para_idx: Some(unit.para_idx),\n"
            "                        recursive_block_prelude_role: RecursiveBlockPreludeRole::None,\n"
            "                    }\n"
            "                })\n"
            "                .collect(),\n"
            "        )\n"
            "    }\n"
            "\n"
            "    fn nested_table_mixed_fragment_heights(\n"
        ),
    ),
    (
        F,
        "                        if anchored_hosted_content_fits {\n",
        (
            f"                        // {TAG} 앞 문단에 줄 배치가 없으면 흐름보다 위로 되돌아가는 저장 vpos 는 낡은 값이다\n"
            "                        let stale_backward_anchor = self.profile.get().hwpx_container()\n"
            "                            && anchored_y - spacing_before + 0.5 < para_y\n"
            "                            && cell.paragraphs[..cp_idx]\n"
            "                                .iter()\n"
            "                                .any(crate::renderer::para_has_no_stored_line_segs);\n"
            "                        if anchored_hosted_content_fits && !stale_backward_anchor {\n"
        ),
    ),
    (
        F,
        (
            "            let legacy_single_cell_empty_spacer = is_block_rowbreak\n"
            "                && table.row_count == 1\n"
            "                && table.col_count == 1\n"
            "                && is_empty_spacer_para\n"
        ),
        (
            "            let legacy_single_cell_empty_spacer = is_block_rowbreak\n"
            "                && table.row_count == 1\n"
            "                && table.col_count == 1\n"
            "                && is_empty_spacer_para\n"
            f"                // {TAG} 줄 배치 없는 HWPX 빈 문단은 접지 않는다(한/글은 한 줄로 조판)\n"
            "                && !(self.profile.get().hwpx_container()\n"
            "                    && crate::renderer::para_has_no_stored_line_segs(p))\n"
        ),
    ),
    (
        # 이어지는 조각의 「앞 조각이 이미 그린 첫 줄 한 줄 건너뛰기」 보정은 legacy 조각용이다.
        # CellUnit 조각(①)은 컷이 정확해 건너뛰면 「서해」 줄이 사라진다
        F,
        (
            "        let compensate_first_visible = recursive_cut.is_none()\n"
            "            && offset > 0.5\n"
        ),
        (
            f"        // {TAG} CellUnit 조각(바깥과 자식 모두 RowBreak, HWPX)은 컷이 정확해 한 줄 건너뛰기 보정을 하지 않는다\n"
            "        let claude_cell_split_child = self.profile.get().hwpx_container()\n"
            "            && matches!(table.page_break, TablePageBreak::RowBreak)\n"
            "            && !table.common.treat_as_char\n"
            "            && nested.is_some_and(|child| {\n"
            "                child.row_count == 1\n"
            "                    && matches!(child.page_break, TablePageBreak::RowBreak)\n"
            "                    && !child.common.treat_as_char\n"
            "            });\n"
            "        let compensate_first_visible = recursive_cut.is_none()\n"
            "            && !claude_cell_split_child\n"
            "            && offset > 0.5\n"
        ),
    ),
    (
        F,
        (
            "        } else if self.profile.get().hwpx_stored_layout()\n"
            "            && terminal\n"
            "            && offset > 0.5\n"
            "            && !first_visible_starts_after_table\n"
        ),
        (
            "        } else if self.profile.get().hwpx_stored_layout()\n"
            "            && !claude_cell_split_child\n"
            "            && terminal\n"
            "            && offset > 0.5\n"
            "            && !first_visible_starts_after_table\n"
        ),
    ),
    (
        # 이어지는 조각의 그리기 창과 흐름 높이에 붙이는 legacy 보정(첫 줄 한 단위, 끝 조각 꼬리)도 CellUnit 조각에는 없다.
        # 9쪽 이어지는 상자가 내용 38px 에 89px 로 그려졌다(한/글 49.6px)
        F,
        (
            "        let terminal_single_cell_tail = recursive_cut.is_none()\n"
            "            && terminal\n"
        ),
        (
            "        let terminal_single_cell_tail = recursive_cut.is_none()\n"
            "            && !claude_cell_split_child\n"
            "            && terminal\n"
        ),
    ),
    (
        F,
        (
            "        } else if is_offset_continuation && !compensate_first_visible {\n"
            "            // Mixed text+nested-table units include a small layout allowance\n"
        ),
        (
            "        } else if is_offset_continuation && !compensate_first_visible && !claude_cell_split_child {\n"
            "            // Mixed text+nested-table units include a small layout allowance\n"
        ),
    ),
    (
        F,
        (
            "        } else if is_offset_continuation && !compensate_first_visible {\n"
            "            flow_visible + first_visible_content_height\n"
        ),
        (
            "        } else if is_offset_continuation && !compensate_first_visible && !claude_cell_split_child {\n"
            "            flow_visible + first_visible_content_height\n"
        ),
    ),
    (
        # 부모 행 높이(쪽 나누기 흐름)에 더하는 42065 끝 조각 보정도 CellUnit 조각에는 없다
        F,
        "                } else if terminal && single_cell_nested_continuation {\n",
        (
            "                } else if terminal\n"
            "                    && single_cell_nested_continuation\n"
            "                    && !self.claude_cell_split_host(table, cell.paragraphs.get(para_idx))\n"
            "                {\n"
        ),
    ),
    (
        F,
        "    pub(crate) fn row_cut_content_height(\n",
        (
            f"    /// {TAG} 이 문단이 품은 1×1 자식 표와 바깥 표가 모두 RowBreak(HWPX CELL)인가 — CellUnit 조각 경로\n"
            "    fn claude_cell_split_host(\n"
            "        &self,\n"
            "        table: &crate::model::table::Table,\n"
            "        para: Option<&crate::model::paragraph::Paragraph>,\n"
            "    ) -> bool {\n"
            "        self.profile.get().hwpx_container()\n"
            "            && matches!(table.page_break, TablePageBreak::RowBreak)\n"
            "            && !table.common.treat_as_char\n"
            "            && para.is_some_and(|p| {\n"
            "                p.controls.iter().any(|control| {\n"
            "                    matches!(control, Control::Table(child)\n"
            "                        if child.row_count == 1\n"
            "                            && matches!(child.page_break, TablePageBreak::RowBreak)\n"
            "                            && !child.common.treat_as_char)\n"
            "                })\n"
            "            })\n"
            "    }\n"
            "\n"
            "    pub(crate) fn row_cut_content_height(\n"
        ),
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
        a, b = find.replace("\n", nl), repl.replace("\n", nl)
        if raw.count(a) != 1:
            sys.exit(
                f"{rel}: 고칠 자리를 하나로 못 찾았다({raw.count(a)}): {find[:60]!r}"
            )
        f.write_bytes(raw.replace(a, b).encode("utf-8"))
    print("되돌림" if revert else "고침", len(EDITS))


if __name__ == "__main__":
    main()
