"""개발용: 붙여넣기와 범위 지우기 뒤 각주, 미주 번호를 문서 순서대로 다시 매긴다.

    python apply_note_renumber.py [--revert]

근거(2026-10-19 사용자 보고): 각주가 든 글을 잘라 다른 쪽에 붙였더니 옛 번호가 그대로 따라왔다. 엔진은 각주를 넣을 때만
(그것도 구역마다 1부터, 각주만) 번호를 다시 매기고 붙여넣기(paste_internal_*), 캐럿 범위 지우기(delete_range_caret_*) 뒤에는
매기지 않았다. 문서 전체를 순서대로(본문 문단, 표 칸, 글상자, 칸 안 표까지) 훑어 각주와 미주를 따로 매긴다. 구역의 번호 방식이
「이어서」면 앞 구역에 이어 세고, 「구역마다」(또는 첫 구역)는 시작 번호부터, 「쪽마다」 구역의 각주는 쪽 나눔에 달려 건드리지 않는다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx note-renumber]"

RENUMBER = f"""    /// {TAG} 각주, 미주 번호를 문서 순서대로 다시 매긴다(붙여넣기, 범위 지우기 뒤).
    pub(crate) fn claude_renumber_notes(&mut self) {{
        use crate::model::footnote::FootnoteNumbering;
        fn walk(paras: &mut [Paragraph], fn_n: &mut Option<u16>, en_n: &mut u16, depth: usize) {{
            if depth > 8 {{
                return;
            }}
            for para in paras.iter_mut() {{
                for ctrl in para.controls.iter_mut() {{
                    match ctrl {{
                        Control::Footnote(f) => {{
                            if let Some(n) = fn_n.as_mut() {{
                                f.number = *n;
                                *n += 1;
                            }}
                        }}
                        Control::Endnote(e) => {{
                            e.number = *en_n;
                            *en_n += 1;
                        }}
                        Control::Table(t) => {{
                            for cell in t.cells.iter_mut() {{
                                walk(&mut cell.paragraphs, fn_n, en_n, depth + 1);
                            }}
                        }}
                        Control::Shape(shape) => {{
                            if let Some(tb) = shape.drawing_mut().and_then(|d| d.text_box.as_mut()) {{
                                walk(&mut tb.paragraphs, fn_n, en_n, depth + 1);
                            }}
                        }}
                        _ => {{}}
                    }}
                }}
            }}
        }}
        let mut fn_count: u16 = 1;
        let mut en_count: u16 = 1;
        for (si, section) in self.document.sections.iter_mut().enumerate() {{
            let fs = &section.section_def.footnote_shape;
            let es = &section.section_def.endnote_shape;
            if si == 0 || fs.numbering == FootnoteNumbering::RestartSection {{
                fn_count = fs.start_number.max(1);
            }}
            if si == 0 || es.numbering == FootnoteNumbering::RestartSection {{
                en_count = es.start_number.max(1);
            }}
            let mut fn_n = (fs.numbering != FootnoteNumbering::RestartPage).then_some(fn_count);
            walk(&mut section.paragraphs, &mut fn_n, &mut en_count, 0);
            if let Some(n) = fn_n {{
                fn_count = n;
            }}
        }}
    }}

    /// 본문 커서 위치의 각주 마커를 조회한다.
"""

WRAP_PASTE = [
    (
        "paste_internal_native",
        "section_idx: usize, para_idx: usize, char_offset: usize",
        "section_idx, para_idx, char_offset",
    ),
    (
        "paste_internal_in_cell_native",
        "section_idx: usize, parent_para_idx: usize, control_idx: usize, cell_idx: usize, cell_para_idx: usize, char_offset: usize",
        "section_idx, parent_para_idx, control_idx, cell_idx, cell_para_idx, char_offset",
    ),
    (
        "paste_internal_in_cell_by_path_native",
        "section_idx: usize, parent_para_idx: usize, path: &[(usize, usize, usize)], char_offset: usize",
        "section_idx, parent_para_idx, path, char_offset",
    ),
]
WRAP_DELETE = [
    (
        "delete_range_caret_native",
        "section_idx: usize, start_para: usize, start_caret: usize, end_para: usize, end_caret: usize, cell_ctx: Option<(usize, usize, usize)>",
        "section_idx, start_para, start_caret, end_para, end_caret, cell_ctx",
    ),
    (
        "delete_range_caret_in_cell_by_path",
        "section_idx: usize, parent_para_idx: usize, path: &[(usize, usize, usize)], start_para: usize, start_caret: usize, end_para: usize, end_caret: usize",
        "section_idx, parent_para_idx, path, start_para, start_caret, end_para, end_caret",
    ),
]


def wrapper(name, params, args):
    return (
        f"    /// {TAG} 끝난 뒤 각주, 미주 번호를 문서 순서대로 다시 매긴다(잘라 붙인 각주가 옛 번호를 가져가던 문제)\n"
        f"    #[allow(clippy::too_many_arguments)]\n"
        f"    pub fn {name}(&mut self, {params}) -> Result<String, HwpError> {{\n"
        f"        let r = self.{name}_claude_inner({args});\n"
        "        if r.is_ok() {\n"
        "            self.claude_renumber_notes();\n"
        "        }\n"
        "        r\n"
        "    }\n\n"
        f"    #[allow(clippy::too_many_arguments)]\n"
        f"    fn {name}_claude_inner(\n"
    )


EDITS = [
    (
        "document_core/commands/footnote_ops.rs",
        "    /// 본문 커서 위치의 각주 마커를 조회한다.\n",
        RENUMBER,
    ),
]
for name, params, args in WRAP_PASTE:
    EDITS.append(
        (
            "document_core/commands/clipboard.rs",
            f"    pub fn {name}(\n",
            wrapper(name, params, args),
        )
    )
for name, params, args in WRAP_DELETE:
    EDITS.append(
        (
            "document_core/commands/text_editing.rs",
            f"    pub fn {name}(\n",
            wrapper(name, params, args),
        )
    )


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
