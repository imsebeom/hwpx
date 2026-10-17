"""개발용: 문서를 열 때 줄 배치가 없는 칸 문단을 다시 짜면서 문단 왼쪽, 오른쪽 여백을 빼지 않던 것을 고친다.

    python apply_cell_margin.py [--revert]

근거: 한/글 2024 는 칸 안에서도 문단 여백을 뺀 폭으로 줄을 나눈다(d014 칸 문단: 칸 폭 38050 - 칸 여백 141×2
- 문단 여백 265+628 = 36875 = 한/글 줄 배치 horzsize). rhwp 의 편집 경로(text_editing.rs)는 이미 여백을 빼는데
문서를 여는 경로(document.rs 두 곳)만 칸 안쪽 폭을 그대로 썼다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx cell-para-margin]"

# (파일, 찾을 글, 바꿀 글, 자리 수)
EDITS = [
    (
        "document_core/commands/document.rs",
        "    fn claude_inline_object_host_without_segs(para: &Paragraph) -> bool {\n",
        f"    /// {TAG} 칸 문단이 줄을 채울 폭 — 칸 안쪽 폭에서 문단 왼쪽, 오른쪽 여백을 뺀다. 편집 경로\n"
        "    /// (text_editing.rs 의 final_width)와 같은 식이다. 한/글 2024 도 칸 안에서 문단 여백을 뺀 폭으로 나눈다.\n"
        "    fn claude_cell_para_width(\n"
        "        para: &Paragraph,\n"
        "        inner_px: f64,\n"
        "        styles: &crate::renderer::style_resolver::ResolvedStyleSet,\n"
        "    ) -> f64 {\n"
        "        let style = styles.para_styles.get(para.para_shape_id as usize);\n"
        "        let margin_left = style.map(|s| s.margin_left).unwrap_or(0.0);\n"
        "        let margin_right = style.map(|s| s.margin_right).unwrap_or(0.0);\n"
        "        (inner_px - margin_left - margin_right).max(0.0)\n"
        "    }\n"
        "\n"
        "    fn claude_inline_object_host_without_segs(para: &Paragraph) -> bool {\n",
        1,
    ),
    (
        "document_core/commands/document.rs",
        "        let width_px = crate::renderer::layout::estimate_text_width_unrounded(&para.text, &style);\n",
        f"        // {TAG} 한/글은 줄 끝 빈칸을 줄 폭에 넣지 않는다. 문단 여백을 뺀 정확한 폭에서는 끝 빈칸 때문에\n"
        "        // 「거의 꽉 참」으로 잘못 보고 가짜 둘째 줄을 붙였다(d314 「현  장 」: 끝 빈칸 포함 91%, 빼면 78%).\n"
        "        let width_px = crate::renderer::layout::estimate_text_width_unrounded(para.text.trim_end(), &style);\n",
        1,
    ),
] + [
    (
        "document_core/commands/document.rs",
        f"{lead}\n"
        "                                    reflow_line_segs(\n"
        "                                        cell_para,\n"
        "                                        ParagraphBox::content_width_px(cell_inner_width, dpi),\n",
        f"{lead}\n"
        "                                    reflow_line_segs(\n"
        "                                        cell_para,\n"
        "                                        ParagraphBox::content_width_px(\n"
        f"                                            Self::claude_cell_para_width(cell_para, cell_inner_width, {styles}),\n"
        "                                            dpi,\n"
        "                                        ),\n",
        1,
    )
    # 두 호출 자리는 글이 같아 바로 앞 주석 줄로 가른다(setup.mjs 블록 패치는 찾을 글이 한 곳이어야 한다).
    # 첫 자리의 styles 는 참조, 둘째 자리는 값이다
    for lead, styles in (
        (
            "                                    // 표 소유자가 이미 확정한 셀 폭을 흔든다.",
            "styles",
        ),
        (
            "                                    // 셀 내용 상자 — 위와 같은 이유로 미스냅.",
            "&styles",
        ),
    )
]


def main():
    revert = "--revert" in sys.argv
    for rel, find, repl, count in EDITS:
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
        if n != count:
            sys.exit(f"{rel}: 자리 {n}곳(기대 {count}) — {find[:50]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel, n)


if __name__ == "__main__":
    main()
