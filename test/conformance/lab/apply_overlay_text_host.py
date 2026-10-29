"""개발용: 글이 있는 문단에 글 앞으로/글 뒤로 배치한 1행 표만 있으면 글 문단으로 조판하고 표는 개체(Shape)로만 넣는다.

    python apply_overlay_text_host.py [--revert]

근거(2026-10-29 결과보고서 사본): 「다. AI 프로젝트 적용」, 「가. 프로젝트 운영 환경 구축」 같은 소제목 문단 18개가 글 + 오른쪽
「활동결과물」 꼬리표(1×1 표, IN_FRONT_OF_TEXT, treatAsChar=0)로 되어 있다. 표가 든 문단은 표 문단 경로로 가는데, 그 경로는
글줄을 표 배치(place_table_with_text)가 함께 넣는다. 글 앞으로 표는 #703 단축(흐름 소비 0, Shape)으로 빠지므로 글줄을 넣는
곳이 없어, 엔진 화면에서 소제목 글이 통째로 사라지고 그 줄 높이(1320)도 세지 않았다. 한/글은 소제목을 그리고 줄 높이만큼
내려간다(15쪽: 소제목 다음 157번 표 66690 이 남은 자리 65862 에 안 들어 16쪽으로). 엔진은 표를 15쪽에 담아 한 쪽 적었다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx overlay-text-host]"

EDITS = [
    (
        "renderer/typeset.rs",
        '            let has_table = self.paragraph_has_table(para);\n            if std::env::var("RHWP_DIAG_FLOW").is_ok() {\n',
        (
            f"            // {TAG} 글 + 글 앞으로/글 뒤로 1행 표뿐인 문단은 글 문단으로(표는 아래 컨트롤 반복문이 Shape 로 넣는다)\n"
            "            let has_table = self.paragraph_has_table(para)\n"
            "                && !(st.profile.hwpx_container()\n"
            "                    && st.col_count == 1\n"
            "                    && claude_overlay_text_host(para));\n"
            '            if std::env::var("RHWP_DIAG_FLOW").is_ok() {\n'
        ),
    ),
    (
        "renderer/typeset.rs",
        "                    Control::Footnote(fn_ctrl) => {\n                        let source = FootnoteSource::Body {\n",
        (
            "                    // [claude-hwpx overlay-text-host] 글 문단으로 조판한 글 앞으로/글 뒤로 표는 흐름을 차지하지 않는 개체다(#703 과 같음)\n"
            "                    Control::Table(t)\n"
            "                        if !has_table\n"
            "                            && !t.common.treat_as_char\n"
            "                            && matches!(\n"
            "                                t.common.text_wrap,\n"
            "                                crate::model::shape::TextWrap::InFrontOfText\n"
            "                                    | crate::model::shape::TextWrap::BehindText\n"
            "                            ) =>\n"
            "                    {\n"
            "                        st.current_items.push(PageItem::Shape {\n"
            "                            para_index: para_idx,\n"
            "                            control_index: ctrl_idx,\n"
            "                        });\n"
            "                    }\n"
            "                    Control::Footnote(fn_ctrl) => {\n"
            "                        let source = FootnoteSource::Body {\n"
        ),
    ),
    (
        "renderer/typeset.rs",
        "fn para_is_empty_topbottom_table_anchor(para: &Paragraph) -> bool {\n",
        (
            "/// [claude-hwpx overlay-text-host] 보이는 글이 있고, 표가 모두 글자처럼 취급이 아닌 1행 글 앞으로/글 뒤로 표인 문단.\n"
            "/// 표 문단 경로에서는 이 표가 흐름 0 Shape 로 빠져 글줄을 넣을 곳이 없다(소제목 + 「활동결과물」 꼬리표).\n"
            "fn claude_overlay_text_host(para: &Paragraph) -> bool {\n"
            "    para_has_non_whitespace_text(para)\n"
            "        && para.controls.iter().any(|c| matches!(c, Control::Table(_)))\n"
            "        && para.controls.iter().all(|c| match c {\n"
            "            Control::Table(t) => {\n"
            "                !t.common.treat_as_char\n"
            "                    && t.row_count <= 1\n"
            "                    && matches!(\n"
            "                        t.common.text_wrap,\n"
            "                        crate::model::shape::TextWrap::InFrontOfText\n"
            "                            | crate::model::shape::TextWrap::BehindText\n"
            "                    )\n"
            "            }\n"
            "            _ => true,\n"
            "        })\n"
            "}\n"
            "\n"
            "fn para_is_empty_topbottom_table_anchor(para: &Paragraph) -> bool {\n"
        ),
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
