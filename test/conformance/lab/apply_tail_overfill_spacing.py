"""개발용: 칸 안 분할에서 마지막 가시 단위가 본문 아래로 넘칠 수 있는 양을 그 줄의 줄 간격으로 제한한다(HWPX).

    python apply_tail_overfill_spacing.py [--revert]

근거(2026-10-18 d087 진단): 1x1 CELL 표(p51, 칸 안 문단 17개)를 쪽에서 가를 때 엔진의 `visible_tail_fits_before_spacer` 는
뒤에 빈 문단(spacer)이 오는 마지막 가시 단위를 「그 단위 높이만큼」 넘쳐도 현재 조각에 남긴다. 줄 간격이 본문 아래로 나가는 것을
허용하려던 규칙인데 상한이 단위 높이 전체라, 171px 그림 줄을 135px 넘쳐 담고 나머지를 다음 쪽으로 넘기지 않았다(d087 5쪽 1071px,
한/글은 그 그림부터 6쪽). 한/글의 마지막 줄 규칙(줄 간격은 본문 밖으로 나가도 된다)대로 넘침을 그 줄의 줄 간격 안으로 묶는다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx tail-overfill-spacing]"

NEW_COND = (
    "                    let visible_tail_before_spacer = relaxed_hard_break\n"
    "                        && Self::visible_tail_fits_before_spacer(&units, j, h, avail_height)\n"
    f"                        // {TAG} 넘침은 그 줄의 줄 간격까지만(HWPX). 단위 높이 전체를 허용해 d087 의 171px 그림 줄이 135px 넘쳤다\n"
    "                        && (!self.profile.get().hwpx_container()\n"
    "                            || h + u.height - avail_height\n"
    "                                <= cell\n"
    "                                    .paragraphs\n"
    "                                    .get(u.para_idx)\n"
    "                                    .and_then(|p| p.line_segs.get(u.vis_start))\n"
    "                                    .map(|s| hwpunit_to_px(s.line_spacing.max(0), self.dpi))\n"
    "                                    .unwrap_or(u.height)\n"
    "                                    + 0.5);\n"
)

EDITS = [
    (
        "renderer/layout/table_layout.rs",
        "                            hit_hard_break = true;\n"
        "                            break;\n"
        "                        }\n"
        "                    }\n"
        "                    let visible_tail_before_spacer = relaxed_hard_break\n"
        "                        && Self::visible_tail_fits_before_spacer(&units, j, h, avail_height);\n",
        "                            hit_hard_break = true;\n"
        "                            break;\n"
        "                        }\n"
        "                    }\n" + NEW_COND,
    ),
    (
        "renderer/layout/table_layout.rs",
        "avail_height, over\n"
        "                            );\n"
        "                        }\n"
        "                    }\n"
        "                    let visible_tail_before_spacer = relaxed_hard_break\n"
        "                        && Self::visible_tail_fits_before_spacer(&units, j, h, avail_height);\n",
        "avail_height, over\n"
        "                            );\n"
        "                        }\n"
        "                    }\n" + NEW_COND,
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
