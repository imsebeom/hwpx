"""개발용: 줄 배치 없는 칸 문단에서 글 없이 글자처럼 취급 도형만 든 줄을 글자 높이로 접지 않는다.

    python apply_cell_tacshape_line.py [--revert]

그리기는 글자처럼 취급 도형이 든 줄의 높이를 글자 기준(max_fs x 1.2)으로 접고, 본문은 문단 바닥값(layout_column_item)이
도형 높이를 되살린다. 칸에는 그 짝이 없어 #1842 가 「글자 크기 0 인 도형 전용 줄」만 접지 않게 했는데, 빈 글 run 의 글자 크기가
잡히면 그대로 접힌다. 한/글 새 조판 d317 3쪽 차례 표(칸 첫 문단 = 묶음 개체 3884, 글 없음): 다음 문단 vpos 6384 = 위 간격 1000
+ 3884 + 줄 간격 500 + 아래 간격 1000. 엔진은 묶음 높이를 접어 아래 글이 모두 49px 위였다. 저장 줄 문서는 칸 문단 vpos 를 따라 맞다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx cell-tacshape-line]"

EDITS = [
    (
        "renderer/layout/paragraph_layout.rs",
        "            } else if has_tac_shape\n"
        "                && !empty_tac_guide_has_explicit_shape_height\n"
        "                && (cell_ctx.is_none() || max_fs > 0.0)\n"
        "                && raw_lh > max_fs * 1.5\n",
        "            } else if has_tac_shape\n"
        "                && !empty_tac_guide_has_explicit_shape_height\n"
        "                && (cell_ctx.is_none() || max_fs > 0.0)\n"
        "                && raw_lh > max_fs * 1.5\n"
        f"                // {TAG} 줄 배치 없는 칸 문단의 글 없는 도형 줄은 접지 않는다(칸에는 문단 바닥값 짝이 없다, d317 차례 표)\n"
        "                && !(cell_ctx.is_some()\n"
        "                    && runs_all_whitespace\n"
        "                    && para.is_some_and(crate::renderer::para_has_no_stored_line_segs))\n",
    ),
    (
        "renderer/layout/table_layout.rs",
        "            let has_stored_para_anchor =\n"
        "                !local_vpos_restart_seen && crate::renderer::first_seg_vpos_is_anchor(para, cp_idx);\n",
        f"            // {TAG} 엔진이 합성한 칸 줄의 vpos(모두 0)는 저장 앵커가 아니다 — 첫 문단도 흐름(위 간격)을 따른다\n"
        "            let has_stored_para_anchor = !local_vpos_restart_seen\n"
        "                && crate::renderer::first_seg_vpos_is_anchor(para, cp_idx)\n"
        "                && !(self.profile.get().hwpx_container()\n"
        "                    && crate::renderer::para_has_no_stored_line_segs(para));\n",
    ),
    (
        "renderer/layout/paragraph_layout.rs",
        "            } else if para_index == 0 && !suppress_column_top_vpos_fallback {\n"
        "                let vpos0_px = para\n"
        "                    .and_then(|p| p.line_segs.first())\n"
        "                    .map(|ls| hwpunit_to_px(ls.vertical_pos, self.dpi))\n"
        "                    .unwrap_or(0.0);\n"
        "                y += spacing_before.min(vpos0_px.max(0.0));\n",
        "            } else if para_index == 0 && !suppress_column_top_vpos_fallback {\n"
        "                let vpos0_px = para\n"
        "                    .and_then(|p| p.line_segs.first())\n"
        "                    .map(|ls| hwpunit_to_px(ls.vertical_pos, self.dpi))\n"
        "                    .unwrap_or(0.0);\n"
        f"                // {TAG} HWPX 의 엔진이 만든 줄(vpos 0 은 증거가 아님)이면 위 간격을 남긴다 — 한/글은 칸 첫 문단을\n"
        "                // 늘 위 간격 자리에 둔다(새 정답본 601/601), 쪽 머리도 같다(pagetop-sb-synth)\n"
        "                if self.profile.get().hwpx_container()\n"
        "                    && para\n"
        "                        .and_then(|p| p.line_segs.first())\n"
        "                        .is_some_and(|ls| ls.tag & LineSeg::TAG_IMPLEMENTATION_PROPERTY != 0)\n"
        "                {\n"
        "                    y += spacing_before;\n"
        "                } else {\n"
        "                    y += spacing_before.min(vpos0_px.max(0.0));\n"
        "                }\n",
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
