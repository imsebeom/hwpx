"""개발용: 그리기의 쪽 vpos 기준점에서 쪽 머리 문단에 그린 위 간격을 뺀다(HWPX).

    python apply_page_base_sb.py [--revert]

그리기(layout)는 쪽의 첫 항목 첫 줄 vpos 를 기준점으로 삼아 뒤 문단을 「단 위 + (vpos − 기준점)」에 둔다. 그런데 쪽 머리 문단의 위 간격은
첫 문단을 그릴 때 따로 더한다(paragraph_layout: 저장 vpos 가 쪽 기준이면 그 vpos, 엔진이 만든 줄이면 위 간격 — pagetop-sb-synth).
기준점이 첫 줄 vpos 그대로라 두 번째 문단부터 위 간격만큼 위로 그려졌다(exp/rendery.py --stored: d110 7쪽 첫 문단 88.6pt 는 한/글과
같고 둘째 문단 204.8 대 209.8). 기준점 = 첫 줄 vpos − 첫 문단에 그린 위 간격.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx page-base-sb]"

EDITS = [
    (
        "renderer/layout.rs",
        "        let vpos_page_base_init: Option<i32> = col_content.items.first().and_then(|item| {\n"
        "            match item {\n"
        "                PageItem::FullParagraph { para_index } => paragraphs\n"
        "                    .get(*para_index)\n"
        "                    .and_then(|p| p.line_segs.first())\n"
        "                    .map(|seg| seg.vertical_pos),\n",
        f"        // {TAG} 쪽 머리 문단에 그린 위 간격(paragraph_layout 의 쪽 머리 규칙과 같은 값)을 기준점에서 뺀다 — 안 빼면 둘째 문단부터\n"
        "        // 위 간격만큼 위로 그려진다(d110 7쪽 둘째 문단 −5pt, 한/글 저장본과 새 조판 모두)\n"
        "        let claude_hwpx = self.profile.get().hwpx_container();\n"
        "        let claude_top_sb_hu = |para_index: usize, seg: &crate::model::paragraph::LineSeg| -> i32 {\n"
        "            if !claude_hwpx {\n"
        "                return 0;\n"
        "            }\n"
        "            let sb_hu = paragraphs\n"
        "                .get(para_index)\n"
        "                .and_then(|p| styles.para_styles.get(p.para_shape_id as usize))\n"
        "                .map(|ps| ((ps.spacing_before * 7200.0 / self.dpi).round() as i32).max(0))\n"
        "                .unwrap_or(0);\n"
        "            if sb_hu == 0 {\n"
        "                return 0;\n"
        "            }\n"
        "            let v = seg.vertical_pos.max(0);\n"
        "            let synth = seg.tag & crate::model::paragraph::LineSeg::TAG_IMPLEMENTATION_PROPERTY != 0;\n"
        "            if para_index == 0 {\n"
        "                sb_hu.min(v)\n"
        "            } else if !synth && v <= sb_hu + 38 {\n"
        "                v\n"
        "            } else {\n"
        "                sb_hu\n"
        "            }\n"
        "        };\n"
        "        let vpos_page_base_init: Option<i32> = col_content.items.first().and_then(|item| {\n"
        "            match item {\n"
        "                PageItem::FullParagraph { para_index } => paragraphs\n"
        "                    .get(*para_index)\n"
        "                    .and_then(|p| p.line_segs.first())\n"
        "                    .map(|seg| seg.vertical_pos - claude_top_sb_hu(*para_index, seg)),\n",
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
