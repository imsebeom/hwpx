"""개발용: 문단 모양의 「한 줄로 입력」(breakSetting lineWrap=SQUEEZE)을 읽고, 쓰고, 칸 문단 조판에 반영한다.

    python apply_para_line_wrap.py [--revert]

근거: 정답본(한/글 2024 재저장)에서 문단 모양 lineWrap 이 SQUEEZE 인 문단 818개 중 812개가 한 줄이다(남은 6개는 강제 줄바꿈).
엔진은 칸(subList)의 lineWrap 만 보고 문단 모양 쪽은 읽지 않아 칸 폭에서 줄을 나눴다(불일치 696건 중 103건).
직렬화도 문단 모양 lineWrap 을 늘 BREAK 로 써서, 에디터로 저장하면 이 설정이 사라졌다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx para-line-wrap]"

EDITS = [
    (
        "model/style.rs",
        "    pub break_latin_word: Option<String>,\n}\n",
        "    pub break_latin_word: Option<String>,\n"
        f"    /// {TAG} HWPX breakSetting@lineWrap 원문(BREAK/SQUEEZE/KEEP). None 이면 BREAK.\n"
        "    /// SQUEEZE(한 줄로 입력)는 한/글이 줄을 나누지 않고 자간을 줄여 한 줄에 넣는다.\n"
        "    pub hwpx_line_wrap: Option<String>,\n"
        "}\n",
    ),
    (
        "model/style.rs",
        "            && self.break_latin_word == other.break_latin_word\n    }\n",
        "            && self.break_latin_word == other.break_latin_word\n"
        "            && self.hwpx_line_wrap == other.hwpx_line_wrap\n"
        "    }\n",
    ),
    (
        "parser/doc_info.rs",
        "        break_latin_word: None,\n        // HWP5 원본에는",
        "        break_latin_word: None,\n"
        f"        // {TAG} HWP5 원본에는 HWPX lineWrap 원문이 없다\n"
        "        hwpx_line_wrap: None,\n"
        "        // HWP5 원본에는",
    ),
    (
        "serializer/doc_info/tests.rs",
        "        break_latin_word: None,\n        hwpx_plain_para_margin: false,\n    };\n",
        "        break_latin_word: None,\n"
        f"        // {TAG}\n"
        "        hwpx_line_wrap: None,\n"
        "        hwpx_plain_para_margin: false,\n"
        "    };\n",
    ),
    (
        "serializer/doc_info/tests.rs",
        "        break_latin_word: None,\n        hwpx_plain_para_margin: false,\n    });\n",
        "        break_latin_word: None,\n"
        "        hwpx_line_wrap: None,\n"
        "        hwpx_plain_para_margin: false,\n"
        "    });\n",
    ),
    (
        "parser/hwpx/header.rs",
        '                    b"widowOrphan" => {\n',
        f"                    // {TAG} 「한 줄로 입력」 원문 보존(조판과 직렬화가 쓴다)\n"
        '                    b"lineWrap" => {\n'
        "                        ps.hwpx_line_wrap = Some(attr_str(&attr));\n"
        "                    }\n"
        '                    b"widowOrphan" => {\n',
    ),
    (
        "serializer/hwpx/header.rs",
        '            ("lineWrap", "BREAK"),\n',
        f"            // {TAG} 읽은 원문을 되쓴다(종전에는 늘 BREAK 라 「한 줄로 입력」이 저장에서 사라졌다)\n"
        '            ("lineWrap", ps.hwpx_line_wrap.as_deref().unwrap_or("BREAK")),\n',
    ),
    (
        "renderer/style_resolver.rs",
        "    /// 문단 앞에서 항상 쪽 나눔 — attr1 bit 19\n    pub page_break_before: bool,\n}\n",
        "    /// 문단 앞에서 항상 쪽 나눔 — attr1 bit 19\n"
        "    pub page_break_before: bool,\n"
        f"    /// {TAG} 문단 모양 「한 줄로 입력」(HWPX lineWrap=SQUEEZE)\n"
        "    pub line_wrap_squeeze: bool,\n"
        "}\n",
    ),
    (
        "renderer/style_resolver.rs",
        "            page_break_before: false,\n        }\n    }\n}\n",
        "            page_break_before: false,\n"
        "            line_wrap_squeeze: false,\n"
        "        }\n    }\n}\n",
    ),
    (
        "renderer/style_resolver.rs",
        "        page_break_before: (ps.attr1 >> 19) & 1 != 0,\n    }\n}\n",
        "        page_break_before: (ps.attr1 >> 19) & 1 != 0,\n"
        '        line_wrap_squeeze: ps.hwpx_line_wrap.as_deref() == Some("SQUEEZE"),\n'
        "    }\n}\n",
    ),
    (
        "document_core/commands/document.rs",
        "        if line_wrap != crate::model::table::CELL_LINE_WRAP_SQUEEZE || para.line_segs.len() < 2 {\n"
        "            return;\n"
        "        }\n",
        f"        // {TAG} 칸의 lineWrap 이 BREAK 여도 문단 모양이 「한 줄로 입력」이면 한/글은 한 줄에 넣는다\n"
        "        // (정답본 818문단 중 812개 한 줄, 나머지는 강제 줄바꿈).\n"
        "        let para_squeeze = styles\n"
        "            .para_styles\n"
        "            .get(para.para_shape_id as usize)\n"
        "            .is_some_and(|s| s.line_wrap_squeeze);\n"
        "        if (line_wrap != crate::model::table::CELL_LINE_WRAP_SQUEEZE && !para_squeeze)\n"
        "            || para.line_segs.len() < 2\n"
        "        {\n"
        "            return;\n"
        "        }\n",
    ),
    (
        "document_core/commands/document.rs",
        "                        ParagraphBox::body_for_style(col_width, para_style, dpi),\n"
        "                        styles,\n"
        "                        dpi,\n"
        "                    );\n"
        "                    body_line_seg_changed = true;\n",
        "                        ParagraphBox::body_for_style(col_width, para_style, dpi),\n"
        "                        styles,\n"
        "                        dpi,\n"
        "                    );\n"
        "                    // 본문 문단도 문단 모양이 「한 줄로 입력」이면 한 줄로(칸 lineWrap 은 없으므로 BREAK)\n"
        "                    Self::claude_squeeze_one_line(para, 0, col_width, styles, dpi);\n"
        "                    body_line_seg_changed = true;\n",
    ),
    (
        "document_core/commands/document.rs",
        "                        ParagraphBox::body_for_style(col_width, para_style, dpi),\n"
        "                        &styles,\n"
        "                        dpi,\n"
        "                    );\n"
        "                    reflowed += 1;\n",
        "                        ParagraphBox::body_for_style(col_width, para_style, dpi),\n"
        "                        &styles,\n"
        "                        dpi,\n"
        "                    );\n"
        "                    Self::claude_squeeze_one_line(para, 0, col_width, &styles, dpi);\n"
        "                    reflowed += 1;\n",
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
            sys.exit(f"{rel}: 자리 {n}곳 — {find[:50]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel)


if __name__ == "__main__":
    main()
