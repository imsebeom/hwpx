"""개발용: 쪽 머리의 글자처럼 취급 표 문단도 위 간격을 그린다(HWPX). 쪽 vpos 기준점에서도 같은 값을 뺀다.

    python apply_tac_top_sb.py [--revert]

d218(한/글 저장본): 쪽 머리마다 위 간격 400 인 글자처럼 취급 표 문단이 vpos 400 에 있다. 그리기의 표 위 간격 블록은 단 위가 아닐 때만
위 간격을 더해, 쪽 전체가 4.0pt 위였다(exp/rendery.py --stored: 1, 2, 4, 6~9쪽 −4.0). 본문 문단의 쪽 머리 규칙(paragraph_layout,
pagetop-sb-synth)과 같게: 저장 줄이고 0 < vpos ≤ 위 간격이면 vpos, 엔진이 만든 줄이거나 vpos 가 위 간격보다 크면 위 간격, vpos 0 이면 안 더함.
구역 첫 문단은 min(위 간격, vpos). 기준점(page-base-sb)은 표 항목에서도 첫 줄 vpos − 이 값.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx tac-top-sb]"

EDITS = [
    (
        "renderer/layout.rs",
        "                        if !is_column_top {\n"
        "                            let spacing_before = styles\n"
        "                                .para_styles\n"
        "                                .get(ps_id)\n"
        "                                .map(|ps| ps.spacing_before)\n"
        "                                .unwrap_or(0.0);\n"
        "                            if spacing_before > 0.0 {\n"
        "                                y_offset += spacing_before;\n"
        "                            }\n"
        "                        }\n"
        "                        if outer_margin_top_px > 0.0 {\n",
        "                        if !is_column_top {\n"
        "                            let spacing_before = styles\n"
        "                                .para_styles\n"
        "                                .get(ps_id)\n"
        "                                .map(|ps| ps.spacing_before)\n"
        "                                .unwrap_or(0.0);\n"
        "                            if spacing_before > 0.0 {\n"
        "                                y_offset += spacing_before;\n"
        "                            }\n"
        "                        } else if self.profile.get().hwpx_container() {\n"
        f"                            // {TAG} 쪽 머리 글자처럼 취급 표도 본문 문단의 쪽 머리 규칙대로 위 간격을 그린다(d218 쪽마다 −4.0pt)\n"
        "                            let sb = styles\n"
        "                                .para_styles\n"
        "                                .get(ps_id)\n"
        "                                .map(|ps| ps.spacing_before.max(0.0))\n"
        "                                .unwrap_or(0.0);\n"
        "                            if let Some(seg) = para.line_segs.first() {\n"
        "                                let v = hwpunit_to_px(seg.vertical_pos.max(0), self.dpi);\n"
        "                                let synth = seg.tag\n"
        "                                    & crate::model::paragraph::LineSeg::TAG_IMPLEMENTATION_PROPERTY\n"
        "                                    != 0;\n"
        "                                let add = if para_index == 0 {\n"
        "                                    sb.min(v)\n"
        "                                } else if !synth && v <= sb + 0.5 {\n"
        "                                    v\n"
        "                                } else {\n"
        "                                    sb\n"
        "                                };\n"
        "                                if sb > 0.0 && add > 0.0 {\n"
        "                                    y_offset += add;\n"
        "                                }\n"
        "                            }\n"
        "                        }\n"
        "                        if outer_margin_top_px > 0.0 {\n",
    ),
    (
        "renderer/layout.rs",
        "                PageItem::Table { para_index, .. } => paragraphs\n"
        "                    .get(*para_index)\n"
        "                    .and_then(|p| p.line_segs.first())\n"
        "                    .map(|seg| seg.vertical_pos),\n",
        "                PageItem::Table { para_index, .. } => paragraphs\n"
        "                    .get(*para_index)\n"
        "                    .and_then(|p| p.line_segs.first())\n"
        f"                    // {TAG} 쪽 머리 글자처럼 취급 표에 그린 위 간격도 뺀다(본문 문단과 같은 값)\n"
        "                    .map(|seg| {\n"
        "                        let tac = paragraphs.get(*para_index).is_some_and(|p| {\n"
        "                            p.controls.iter().any(|c| matches!(c, Control::Table(t) if t.common.treat_as_char))\n"
        "                        });\n"
        "                        seg.vertical_pos - if tac { claude_top_sb_hu(*para_index, seg) } else { 0 }\n"
        "                    }),\n",
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
