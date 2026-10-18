"""개발용: HWPX 저장 줄 배치(쪽 기준 vpos)는 표, 개체 항목 뒤에도 그리기의 쪽 vpos 기준점을 버리지 않는다.

    python apply_keep_stored_base.py [--revert]

그리기는 표, 개체(글자처럼 취급 포함) 항목 뒤 기준점을 버리고(「LINE_SEG lh 가 개체 높이를 담아 순차 y 와 어긋난다」) 다음 문단에서 순차 y 로
lazy 기준점을 다시 셈한다. 그런데 순차 y 는 개체 줄의 줄 간격을 빠뜨려 기준점이 그만큼 어긋난다(d334 2쪽: p4 글자처럼 취급 도형 줄
3327 + 간격 780 뒤 lazy 기준점 780, p5 뒤 p6 표가 7.8pt 위. 한/글 저장 vpos 6187 = 3327 + 780 + 1300 + 780).
한/글이 저장한 HWPX 줄 배치는 쪽 기준 절대 좌표라, 기준점이 이미 쪽 경로(vpos_page_base)로 서 있고 이 항목 문단의 줄이 저장 줄이면 그대로 둔다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx keep-stored-base]"

EDITS = [
    (
        "renderer/layout.rs",
        "            if was_tac || (is_table_or_shape && !is_para_float_table && !is_inline_tac_object) {\n"
        "                hcursor.vpos_page_base = None;\n"
        "                hcursor.vpos_lazy_base = None;\n"
        "            }\n",
        f"            // {TAG} 한/글 HWPX 저장 줄 배치는 쪽 기준 절대 좌표 — 쪽 경로 기준점이 서 있고 이 항목 문단 줄이 저장 줄이면 버리지 않는다\n"
        "            // (버리면 순차 y 로 다시 센 lazy 기준점이 개체 줄 간격만큼 어긋난다. d334 2쪽 p6 표 7.8pt 위)\n"
        "            let claude_keep_stored_base = self.profile.get().hwpx_container()\n"
        "                && hcursor.vpos_page_base.is_some()\n"
        "                && paragraphs\n"
        "                    .get(item.para_index())\n"
        "                    .and_then(|p| p.line_segs.first())\n"
        "                    .is_some_and(|s| s.tag & crate::model::paragraph::LineSeg::TAG_IMPLEMENTATION_PROPERTY == 0);\n"
        "            if (was_tac || (is_table_or_shape && !is_para_float_table && !is_inline_tac_object))\n"
        "                && !claude_keep_stored_base\n"
        "            {\n"
        "                hcursor.vpos_page_base = None;\n"
        "                hcursor.vpos_lazy_base = None;\n"
        "            }\n",
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
