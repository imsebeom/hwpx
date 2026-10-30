"""개발용: 오프셋 개체 위에 들어가는 글자처럼 취급 표 줄(tac_above_offset_float_flow)을 문단 맨 위로 되돌릴 때, 저장 밴드가
「바깥 위 여백 + 표 + 바깥 아래 여백」이면 위 여백을 다시 더한다(HWPX).

    python apply_offset_float_om.py [--revert]

근거(회귀 모음 「보도자료_OECD교육지표2026」 c18, 구역 2 53번 문단): 글자처럼 취급 그림 둘 뒤에 6×6 표(바깥 여백 283, 높이 9390,
줄 높이 9956 = 283 + 9390 + 283). 한/글은 표 위 테두리를 줄 맨 위 + 283(733.3px)에 그리는데, 엔진은 이 규칙이 y 를 para_y 로 되돌리며
앞에서 더한 위 여백을 버려 줄 맨 위(730.4px)에 그렸다. 종전에는 0, 1행이 커서 2행부터 우연히 맞았고, tac-no-shrink-hwpx 로 행이
맞아지자 표 전체가 3.6px 위로 드러났다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx offset-float-om]"

EDITS = [
    (
        "renderer/layout.rs",
        (
            "            if tac_above_offset_float_flow.is_some() {\n"
            "                y_offset = para_y_for_table;\n"
            "            }\n"
        ),
        (
            "            if tac_above_offset_float_flow.is_some() {\n"
            "                y_offset = para_y_for_table;\n"
            f"                // {TAG} 저장 밴드가 바깥 위 여백 + 표 + 바깥 아래 여백이면 표는 줄 맨 위 + 위 여백(c18 6×6 표: 한/글 +283)\n"
            "                if self.profile.get().hwpx_container() {\n"
            "                    if let Some(Control::Table(t)) = para.controls.get(control_index) {\n"
            "                        if Self::tac_stored_band_is_outer_box(para, t) {\n"
            "                            y_offset += hwpunit_to_px(t.outer_margin_top as i32, self.dpi);\n"
            "                        }\n"
            "                    }\n"
            "                }\n"
            "            }\n"
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
