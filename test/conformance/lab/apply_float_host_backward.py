"""개발용: 앞 문단이 표만 담은 문단 기준 자리 차지 표 호스트면, 그리기 vpos 보정이 이 문단 위 간격 + 8px 까지 뒤로 당기는 것을 허용한다.

    python apply_float_host_backward.py [--revert]

위 간격이 표 아래에 묻히는 자리(tbl-next-sb, synth-vpos-absorb)에서 순차 y 는 위 간격을 더해 내려가 있다. vpos 보정은 맞는 자리(d189 p6
766.47px)를 내지만 한 번에 뒤로 8px 까지만 허용(Task #643)해 15px 되돌림이 막혔고, 1쪽 남은 글이 11.25pt 아래로 그려졌다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx float-host-backward]"

EDITS = [
    (
        "renderer/height_cursor.rs",
        "            allow_large_backward,\n"
        "            self.dpi,\n"
        "        );\n"
        "        let prev_line_spacing_px",
        "            allow_large_backward,\n"
        "            self.dpi,\n"
        "        );\n"
        f"        // {TAG} 앞 문단이 표만 담은 문단 기준 자리 차지 표 호스트면 이 문단 위 간격은 표 아래에 묻힌다 — 그만큼 뒤로 당겨도 된다(d189 p6)\n"
        "        let claude_prev_float_host = !para_has_visible_text(prev_para)\n"
        "            && prev_para.controls.iter().any(|c| {\n"
        "                matches!(c, Control::Table(t)\n"
        "                    if !t.common.treat_as_char\n"
        "                        && matches!(t.common.text_wrap, TextWrap::TopAndBottom)\n"
        "                        && matches!(t.common.vert_rel_to, crate::model::shape::VertRelTo::Para))\n"
        "            });\n"
        "        let applied = applied\n"
        "            || (claude_prev_float_host\n"
        "                && end_y >= y_offset - curr_sb - 8.0\n"
        "                && end_y >= self.col_area_y\n"
        "                && end_y <= self.col_area_y + self.col_area_height);\n"
        "        let prev_line_spacing_px",
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
