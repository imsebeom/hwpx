"""개발용: 여백과 들여쓰기를 뺀 가장 좁은 줄 폭이 줄 폭의 25% 미만이면 그 문단의 왼쪽, 오른쪽 여백과 들여쓰기를 모두 무시한다.

    python apply_narrow_margin_ignore.py [--revert]

근거(2026-10-18 d322 사본 한/글 실험, exp/make_hanging.py): 칸(줄 폭 5824) 문단의 내어쓰기를 바꿔 재저장 줄 시작을 보니 4350(남는 폭 1474)까지는
지키고 4400(1424)부터 들여쓰기 0 과 같은 줄이 된다. 경계 1456 = 줄 폭의 25%. 정답본 줄 기록에서도 이런 문단은 왼쪽, 오른쪽 여백까지 무시한다
(d033, d159: 칸 2440 에 여백 1000+1000 → horzpos 0, d334: 1440 에 여백 200 + 내어쓰기 1200 → horzpos 0). 엔진은 내어쓰기를 지켜 d322 칸
1297, 1309 를 한두 글자마다 꺾어 칸이 매우 길어졌다. 줄 나눔(본문 상자, 칸 문단 폭, 편집 경로 폭, 들여쓰기 두 경로)과 화면 배치에 같은 판정을 쓴다.
줄 나눔의 들여쓰기 판정은 상자 폭 + 여백을 원래 줄 폭으로 본다(여백을 무시한 문단은 상자가 이미 원래 폭이라 조금 크게 잡히지만 판정은 같다).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx narrow-margin-ignore]"

EDITS = [
    (
        "renderer/style_resolver.rs",
        "/// DocInfo 참조 테이블을 해소된 스타일 목록으로 변환한다.\n",
        f"/// {TAG} 줄 폭(여백 적용 전, px)에서 왼쪽, 오른쪽 여백과 들여쓰기(양쪽 모두)를 뺀 가장 좁은 줄이 줄 폭의 25% 미만이면 한/글은\n"
        "/// 그 문단의 여백과 들여쓰기를 모두 무시한다(d322 사본 실험: 줄 폭 5824 에서 남는 폭 1474 지킴, 1424 무시, 경계 1456).\n"
        "pub(crate) fn claude_margins_ignored(style: &ResolvedParaStyle, full_px: f64) -> bool {\n"
        "    let used = style.margin_left.max(0.0) + style.margin_right.max(0.0) + style.indent.abs();\n"
        "    used > 0.0 && full_px > 0.0 && full_px - used < full_px * 0.25\n"
        "}\n"
        "\n"
        "/// DocInfo 참조 테이블을 해소된 스타일 목록으로 변환한다.\n",
    ),
    (
        "renderer/layout_frame.rs",
        "        let margin_left = style.map(|s| s.margin_left).unwrap_or(0.0);\n"
        "        let margin_right = style.map(|s| s.margin_right).unwrap_or(0.0);\n"
        "        let head_type = style.map(|s| s.head_type).unwrap_or(HeadType::None);\n",
        f"        // {TAG} 남는 폭이 25% 미만이면 여백을 무시한다\n"
        "        let claude_ignored = style\n"
        "            .is_some_and(|s| crate::renderer::style_resolver::claude_margins_ignored(s, column_width_px));\n"
        "        let margin_left = if claude_ignored { 0.0 } else { style.map(|s| s.margin_left).unwrap_or(0.0) };\n"
        "        let margin_right = if claude_ignored { 0.0 } else { style.map(|s| s.margin_right).unwrap_or(0.0) };\n"
        "        let head_type = style.map(|s| s.head_type).unwrap_or(HeadType::None);\n",
    ),
    (
        "document_core/commands/document.rs",
        "        let style = styles.para_styles.get(para.para_shape_id as usize);\n"
        "        let margin_left = style.map(|s| s.margin_left).unwrap_or(0.0);\n"
        "        let margin_right = style.map(|s| s.margin_right).unwrap_or(0.0);\n"
        "        (inner_px - margin_left - margin_right).max(0.0)\n",
        "        let style = styles.para_styles.get(para.para_shape_id as usize);\n"
        f"        // {TAG} 남는 폭이 25% 미만이면 여백을 무시한다\n"
        "        if style.is_some_and(|s| crate::renderer::style_resolver::claude_margins_ignored(s, inner_px)) {\n"
        "            return inner_px;\n"
        "        }\n"
        "        let margin_left = style.map(|s| s.margin_left).unwrap_or(0.0);\n"
        "        let margin_right = style.map(|s| s.margin_right).unwrap_or(0.0);\n"
        "        (inner_px - margin_left - margin_right).max(0.0)\n",
    ),
    (
        "document_core/commands/text_editing.rs",
        "        let para_style = styles.para_styles.get(para_shape_id as usize);\n"
        "        let margin_left = para_style.map(|s| s.margin_left).unwrap_or(0.0);\n"
        "        let margin_right = para_style.map(|s| s.margin_right).unwrap_or(0.0);\n"
        "        let final_width = (available_width - margin_left - margin_right).max(0.0);\n",
        "        let para_style = styles.para_styles.get(para_shape_id as usize);\n"
        "        let margin_left = para_style.map(|s| s.margin_left).unwrap_or(0.0);\n"
        "        let margin_right = para_style.map(|s| s.margin_right).unwrap_or(0.0);\n"
        f"        // {TAG} 남는 폭이 25% 미만이면 여백을 무시한다\n"
        "        let final_width = if para_style\n"
        "            .is_some_and(|s| crate::renderer::style_resolver::claude_margins_ignored(s, available_width))\n"
        "        {\n"
        "            available_width\n"
        "        } else {\n"
        "            (available_width - margin_left - margin_right).max(0.0)\n"
        "        };\n",
    ),
    (
        "document_core/commands/text_editing.rs",
        "        let para_style = styles.para_styles.get(cell_para.para_shape_id as usize);\n"
        "        let margin_left = para_style.map(|s| s.margin_left).unwrap_or(0.0);\n"
        "        let margin_right = para_style.map(|s| s.margin_right).unwrap_or(0.0);\n"
        "        let final_width = (available_width - margin_left - margin_right).max(0.0);\n",
        "        let para_style = styles.para_styles.get(cell_para.para_shape_id as usize);\n"
        "        let margin_left = para_style.map(|s| s.margin_left).unwrap_or(0.0);\n"
        "        let margin_right = para_style.map(|s| s.margin_right).unwrap_or(0.0);\n"
        f"        // {TAG} 남는 폭이 25% 미만이면 여백을 무시한다\n"
        "        let final_width = if para_style\n"
        "            .is_some_and(|s| crate::renderer::style_resolver::claude_margins_ignored(s, available_width))\n"
        "        {\n"
        "            available_width\n"
        "        } else {\n"
        "            (available_width - margin_left - margin_right).max(0.0)\n"
        "        };\n",
    ),
    (
        "renderer/composer/line_breaking.rs",
        "    let indent_px = indent_override.unwrap_or_else(|| para_style.map(|style| style.indent).unwrap_or(0.0));\n",
        "    let indent_px = indent_override.unwrap_or_else(|| para_style.map(|style| style.indent).unwrap_or(0.0));\n"
        f"    // {TAG} 남는 폭이 25% 미만이면 들여쓰기를 무시한다(상자 폭 + 여백 = 원래 줄 폭)\n"
        "    let indent_px = if para_style.is_some_and(|s| {\n"
        "        let box_px = hwpunit_to_px(frame.horizontal.end - frame.horizontal.start, dpi);\n"
        "        crate::renderer::style_resolver::claude_margins_ignored(s, box_px + s.margin_left + s.margin_right)\n"
        "    }) {\n"
        "        0.0\n"
        "    } else {\n"
        "        indent_px\n"
        "    };\n",
    ),
    (
        "renderer/composer/line_breaking.rs",
        "    let indent_px = claude_indent_override.unwrap_or_else(|| para_style.map(|s| s.indent).unwrap_or(0.0));\n",
        "    let indent_px = claude_indent_override.unwrap_or_else(|| para_style.map(|s| s.indent).unwrap_or(0.0));\n"
        f"    // {TAG} 남는 폭이 25% 미만이면 들여쓰기를 무시한다(상자 폭 + 여백 = 원래 줄 폭)\n"
        "    let indent_px = if para_style.is_some_and(|s| {\n"
        "        let box_px = hwpunit_to_px(seg_width_hwp, dpi);\n"
        "        crate::renderer::style_resolver::claude_margins_ignored(s, box_px + s.margin_left + s.margin_right)\n"
        "    }) {\n"
        "        0.0\n"
        "    } else {\n"
        "        indent_px\n"
        "    };\n",
    ),
    (
        "renderer/layout/paragraph_layout.rs",
        "        let box_margin_left = para_style.map(|s| s.margin_left).unwrap_or(0.0);\n"
        "        let box_margin_right = para_style.map(|s| s.margin_right).unwrap_or(0.0);\n"
        "        let indent = para_style.map(|s| s.indent).unwrap_or(0.0);\n",
        f"        // {TAG} 남는 폭이 25% 미만이면 여백과 들여쓰기를 모두 무시한다(줄 나눔과 같은 판정)\n"
        "        let claude_ignored = para_style\n"
        "            .is_some_and(|s| crate::renderer::style_resolver::claude_margins_ignored(s, col_area.width));\n"
        "        let box_margin_left = if claude_ignored { 0.0 } else { para_style.map(|s| s.margin_left).unwrap_or(0.0) };\n"
        "        let box_margin_right = if claude_ignored { 0.0 } else { para_style.map(|s| s.margin_right).unwrap_or(0.0) };\n"
        "        let indent = if claude_ignored { 0.0 } else { para_style.map(|s| s.indent).unwrap_or(0.0) };\n",
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
