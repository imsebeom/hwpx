"""개발용: 글 없는 문단에 위아래 배치 표 하나만 든 경우(empty-host-block)의 흐름 전진에 위, 아래 캡션을 넣는다(HWPX).

    python apply_empty_host_caption.py [--revert]

교사개발자 가이드북 파트2 합본 60쪽: 표 5-2(6x2, 글자처럼 취급 아님, 아래 캡션 「표 5-2. 개발 단계별 점검」)를 담은 빈 문단의
흐름 전진을 「선언 높이 + 오프셋 + 바깥 여백 위아래」로만 잡아 캡션 간격과 캡션 줄(약 24.6px)이 빠졌다. 그리기는 캡션까지 그리므로
뒤 내용이 조판보다 아래에 그려져 쪽 끝 본문 줄이 각주 구역과 겹쳤다. 한/글 재저장본: 표 문단 vpos 11616 → 다음 문단 46645,
차이 35029 = 표 높이 32613 + 바깥 여백 283 x 2 + 캡션 간격 850 + 캡션 줄 높이 1000(줄 간격 제외).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx empty-host-caption]"

EDITS = [
    (
        "renderer/typeset.rs",
        "                let body = if declared > 1.0 { declared } else { table_total_height };\n"
        "                st.current_height += pre_height + body + hwpunit_to_px(extras_hu as i32, self.dpi);\n",
        "                let body = if declared > 1.0 { declared } else { table_total_height };\n"
        f"                // {TAG} 선언 높이는 캡션을 품지 않는다 — 위, 아래 캡션은 캡션 간격 + 캡션 줄 높이를 더한다(한/글 재저장본, 가이드북 파트2 표 5-2)\n"
        "                let claude_caption = match table.caption.as_ref() {\n"
        "                    Some(cap)\n"
        "                        if declared > 1.0\n"
        "                            && matches!(\n"
        "                                cap.direction,\n"
        "                                crate::model::shape::CaptionDirection::Top\n"
        "                                    | crate::model::shape::CaptionDirection::Bottom\n"
        "                            ) =>\n"
        "                    {\n"
        "                        let h = crate::renderer::composer::caption_height_px(&table.caption, self.dpi);\n"
        "                        if h > 0.0 { h + hwpunit_to_px(cap.spacing as i32, self.dpi) } else { 0.0 }\n"
        "                    }\n"
        "                    _ => 0.0,\n"
        "                };\n"
        "                st.current_height += pre_height + body + claude_caption + hwpunit_to_px(extras_hu as i32, self.dpi);\n",
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
