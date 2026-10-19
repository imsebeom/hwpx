"""개발용: HWPX 의 엔진이 만든 줄에서 글자처럼 취급 표가 놓인 줄을 컨트롤 위치로 찾는다(그리기).

    python apply_tac_synth_line_seg.py [--revert]

그리기는 글자처럼 취급 표의 줄을 HWP5 저장 문서만 control_line_seg_index(컨트롤 글자 위치 → 줄)로 찾고, HWPX 는 컨트롤 번호를 줄 번호로
쓴다(저장 사다리가 아니라 사영이 성립하지 않는다는 #4531 주석). 엔진이 만든 줄은 엔진이 글자 위치로 나눈 것이라 사영이 성립한다.
한 문단에 글자처럼 취급 표가 줄마다 하나씩 있으면(d321 p0: 구역, 단 정의 뒤 표 둘, 줄 5418 + 960, 10069 + 600) 첫 표의 줄(번호 2)을 못 찾아
다음 표까지의 간격 960 을 더하지 않았다. 한/글은 둘째 표 줄을 6378 = 5418 + 960 에 둔다(엔진 20.4px 위, 쪽 전체 23.7px 위).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx tac-synth-line-seg]"

EDITS = [
    (
        "renderer/layout.rs",
        "                let seg_idx = if self.profile.get().hwp5_stored_pagination_layout() {\n"
        "                    control_line_seg_index(para, control_index).unwrap_or(control_index)\n"
        "                } else {\n",
        "                let seg_idx = if self.profile.get().hwp5_stored_pagination_layout()\n"
        f"                    // {TAG} 엔진이 만든 줄은 글자 위치로 나눈 것이라 사영이 성립한다(d321 p0)\n"
        "                    || (self.profile.get().hwpx_container()\n"
        "                        && crate::renderer::para_has_no_stored_line_segs(para))\n"
        "                {\n"
        "                    control_line_seg_index(para, control_index).unwrap_or(control_index)\n"
        "                } else {\n",
    ),
    (
        "renderer/layout.rs",
        "                        let gap = next_seg.vertical_pos - (seg.vertical_pos + seg.line_height);\n"
        "                        y_offset += hwpunit_to_px(gap, self.dpi);\n",
        "                        let gap = next_seg.vertical_pos - (seg.vertical_pos + seg.line_height);\n"
        "                        y_offset += hwpunit_to_px(gap, self.dpi);\n"
        f"                        // {TAG} 줄 높이는 바깥 여백 위아래를 담는다 — 표 바닥 뒤 아래 여백까지가 줄 끝이다\n"
        "                        if self.profile.get().hwpx_container()\n"
        "                            && crate::renderer::para_has_no_stored_line_segs(para)\n"
        "                        {\n"
        "                            y_offset += hwpunit_to_px(t.outer_margin_bottom as i32, self.dpi);\n"
        "                        }\n",
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
