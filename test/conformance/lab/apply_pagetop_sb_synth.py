"""개발용: 엔진이 만든 줄(줄 배치 없는 HWPX, 편집 뒤 다시 만든 줄)의 쪽 머리 문단도 위 간격을 그린다(HWPX).

    python apply_pagetop_sb_synth.py [--revert]

한/글 새 조판(exp/harvest_pagetop_sb.py, out/fresh/rt): 쪽 머리 본문 문단의 위 간격은 256건 모두 첫 줄 vpos = 위 간격으로 남는다
(쪽 나누기 60, 흐름 196, vpos 0 은 0건). 그리기(paragraph_layout)는 쪽 머리에서 위 간격을 버리고 저장 줄의 vpos 가 증거일 때만
되살렸다(Task #1811). 엔진이 만든 줄에는 그 증거가 없어 쪽 전체가 위 간격만큼 위로 그려졌다(exp/rendery.py: d110 6쪽 -10pt,
7쪽 -5pt). 조판(쪽 나눔)은 이미 위 간격을 센다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx pagetop-sb-synth]"

EDITS = [
    (
        "renderer/layout/paragraph_layout.rs",
        "                if vpos0_px > 0.0 && vpos0_px <= spacing_before + 0.5 {\n"
        "                    y += vpos0_px;\n"
        "                }\n",
        "                if vpos0_px > 0.0 && vpos0_px <= spacing_before + 0.5 {\n"
        "                    y += vpos0_px;\n"
        f"                }} else if self.profile.get().hwpx_container()\n"
        "                    && para.and_then(|p| p.line_segs.first()).is_some_and(|ls| {\n"
        "                        ls.tag & LineSeg::TAG_IMPLEMENTATION_PROPERTY != 0\n"
        "                            || hwpunit_to_px(ls.vertical_pos, self.dpi) > spacing_before + 0.5\n"
        "                    })\n"
        "                {\n"
        f"                    // {TAG} 엔진이 만든 줄이거나 첫 줄 vpos 가 쪽 기준이 아니면(구역 처음부터 이어 센 값) 쪽 머리 증거가 없다 —\n"
        "                    // 한/글 HWPX 는 쪽 머리 위 간격을 늘 남긴다(새 조판 256/256). vpos 0(트림한 저장본)은 그대로 버린다\n"
        "                    y += spacing_before;\n"
        "                }\n",
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
