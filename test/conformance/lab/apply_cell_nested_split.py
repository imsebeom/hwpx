"""개발용: 「셀 단위로 나눔」 표 칸 안의 「셀 단위로 나눔」 1×1 중첩 표는 한 쪽보다 작아도 쪽 끝에서 나눈다.

    python apply_cell_nested_split.py [--revert]

근거(사본 실험, 한국문화 1단원 삽입본 「푸른 바다로 둘러싸여 있어요」 상자, scratchpad mkvar.py → 한/글 2024 PDF):
바깥 1×1 표(CELL) 칸에 글 세 줄과 1×1 중첩 표(그림 문단 + 글 세 줄, 선언 높이 22224)가 있다.
  - 바깥 CELL, 안 CELL: 한/글은 안 표를 쪽 끝에서 나눈다(그림과 「동해」 줄은 앞 쪽, 「서해」부터 다음 쪽)
  - 바깥 CELL, 안 TABLE/NONE: 안 표를 통째로 다음 쪽으로(엔진도 같다)
  - 바깥 TABLE: 바깥 표를 통째로 다음 쪽으로(엔진은 나눈다 — 이 패치 밖)
엔진은 1×1 자식 표를 한 쪽을 넘을 때만 조각으로 나눠 앞 경우에도 통째로 넘겼다.
SRC 는 스킬 빌드 소스(~/.claude/skills/hwpx/editor/.build/rhwp/src)다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx cell-nested-split]"

EDITS = [
    (
        "renderer/layout/table_layout.rs",
        "                    if frags.len() > 1\n"
        "                        && (total_frag_h > multi_page_px\n"
        "                            || exceeds_physical_page\n"
        "                            || native_short_parent_child_fragment\n"
        "                            || stored_frame_tail_before_next_para)\n",
        f"                    // {TAG} 바깥 표와 자식 표가 모두 「셀 단위로 나눔」(HWPX CELL, 모델 RowBreak)이면\n"
        "                    // 한/글은 한 쪽보다 작은 1×1 자식 표도 쪽 끝에서 나눈다(한국문화 1단원 사본 실험).\n"
        "                    let cell_split_child = matches!(\n"
        "                        table.page_break,\n"
        "                        crate::model::table::TablePageBreak::RowBreak\n"
        "                    ) && matches!(nt.page_break, crate::model::table::TablePageBreak::RowBreak)\n"
        "                        && !table.common.treat_as_char\n"
        "                        && !nt.common.treat_as_char;\n"
        "                    if frags.len() > 1\n"
        "                        && (total_frag_h > multi_page_px\n"
        "                            || exceeds_physical_page\n"
        "                            || native_short_parent_child_fragment\n"
        "                            || stored_frame_tail_before_next_para\n"
        "                            || cell_split_child)\n",
    ),
    (
        # 나눈 조각은 세로 정렬을 위로 바꿔 칸 문단을 저장 vpos 에 붙이는데, 앞 문단에 줄 배치가 없으면
        # (스크립트가 그림을 넣고 줄 배치를 지운 칸) 뒤 문단의 저장 vpos 는 그 그림을 모르는 낡은 값이다.
        # 그 값이 흐름보다 위면 붙이지 않는다(사본: 「동해」 줄이 지도 위에 겹쳐 그려졌다)
        "renderer/layout/table_layout.rs",
        "                        if anchored_hosted_content_fits {\n",
        f"                        // {TAG} 앞 문단에 줄 배치가 없으면 흐름보다 위로 되돌아가는 저장 vpos 는 낡은 값이다\n"
        "                        let stale_backward_anchor = self.profile.get().hwpx_container()\n"
        "                            && anchored_y - spacing_before + 0.5 < para_y\n"
        "                            && cell.paragraphs[..cp_idx]\n"
        "                                .iter()\n"
        "                                .any(crate::renderer::para_has_no_stored_line_segs);\n"
        "                        if anchored_hosted_content_fits && !stale_backward_anchor {\n",
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
            sys.exit(f"{rel}: 고칠 자리를 하나로 못 찾았다({raw.count(a)})")
        f.write_bytes(raw.replace(a, b).encode("utf-8"))
        print("고침:", rel)


if __name__ == "__main__":
    main()
