"""개발용: 줄 배치 없는 문단에 글자처럼 취급 표가 여럿이면 다음 표 줄은 「앞 표 + 바깥 아래 여백 + 줄 간격」 뒤에서 시작하고,
다음 표는 그 줄 위에서 바깥 위 여백만큼 내려 그린다.

    python apply_tac_multi_om.py [--revert]

근거(한국문화 1단원 삽입본 1쪽 pi=3, 한/글 2024 PDF): 빈 문단에 글자처럼 취급 표 둘(지도 표, 설명 상자),
바깥 여백 위 283 아래 1417, 문단 줄 간격 15%(15pt 글자 → -1275HU = -17px).
한/글은 첫 표 바닥 655.0px, 둘째 표 위 660.6px(5.6px = 18.9 - 17 + 3.8). 엔진은 첫 표 바닥에 줄 간격만 더해(-17px)
둘째 표가 첫 표 아래 17px 를 덮었다. 엔진이 만든 줄의 줄 높이는 표와 바깥 여백 위아래를 담는다.
저장 줄 배치가 있는 문단(#5729 저장 밴드)은 종전대로 둔다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx tac-multi-om]"
F = "renderer/layout.rs"

EDITS = [
    (
        F,
        (
            "                        let gap = next_seg.vertical_pos - (seg.vertical_pos + seg.line_height);\n"
            "                        y_offset += hwpunit_to_px(gap, self.dpi);\n"
        ),
        (
            "                        let gap = next_seg.vertical_pos - (seg.vertical_pos + seg.line_height);\n"
            "                        y_offset += hwpunit_to_px(gap, self.dpi);\n"
            f"                        // {TAG} 엔진이 만든 줄의 높이는 표와 바깥 여백 위아래를 담는다 — 다음 줄은\n"
            "                        // 표 바닥 + 바깥 아래 여백 + 줄 간격에서 시작한다(한국문화 1단원 1쪽 한/글 PDF)\n"
            "                        if self.profile.get().hwpx_container()\n"
            "                            && crate::renderer::para_has_no_stored_line_segs(para)\n"
            "                        {\n"
            "                            if let Some(Control::Table(cur)) = para.controls.get(control_index) {\n"
            "                                y_offset += hwpunit_to_px(cur.outer_margin_bottom as i32, self.dpi);\n"
            "                            }\n"
            "                        }\n"
        ),
    ),
    (
        F,
        "                        if Self::tac_stored_band_is_outer_box(para, t) {\n",
        (
            f"                        // {TAG} 엔진이 만든 줄도 표 위에 바깥 위 여백을 둔다\n"
            "                        if Self::tac_stored_band_is_outer_box(para, t)\n"
            "                            || (self.profile.get().hwpx_container()\n"
            "                                && crate::renderer::para_has_no_stored_line_segs(para))\n"
            "                        {\n"
        ),
    ),
]


def main():
    revert = "--revert" in sys.argv
    for rel, find, repl in EDITS:
        if revert:
            find, repl = repl, find
        f = SRC / rel
        raw = f.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        a, b = find.replace("\n", nl), repl.replace("\n", nl)
        if raw.count(a) != 1:
            sys.exit(
                f"{rel}: 고칠 자리를 하나로 못 찾았다({raw.count(a)}): {find[:50]!r}"
            )
        f.write_bytes(raw.replace(a, b).encode("utf-8"))
    print("되돌림" if revert else "고침", len(EDITS))


if __name__ == "__main__":
    main()
