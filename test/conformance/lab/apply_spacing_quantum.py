"""개발용: 비율 줄 간격을 한/글처럼 「반올림(내림(줄 높이/4) × (비율-100)/100) × 4」로 잰다.

    python apply_spacing_quantum.py [--revert]

근거(harvest_spacing.py --check): 정답본(한/글 2024 재저장) 줄 기록 105,341줄에서 종전 식 「반올림(높이×(비율-100)/100/4)×4」는
95.93%, 이 식은 96.60% 와 맞는다. 차이는 동점(.5)에서 난다 — 10.5pt 160% 는 630 이 아니라 628, 9pt 130% 는 272.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx spacing-quantum]"

EDITS = [
    (
        "renderer/composer/line_breaking.rs",
        "                let spacing = line_height_hwp as f64 * (ls_value - 100.0) / 100.0;\n"
        "                if spacing > 0.0 {\n"
        "                    (spacing / 4.0 + 0.5 + 1e-6).floor() as i32 * 4\n",
        "                let spacing = line_height_hwp as f64 * (ls_value - 100.0) / 100.0;\n"
        "                if spacing > 0.0 {\n"
        f"                    // {TAG} 줄 높이를 먼저 4 단위로 내린 뒤 비율을 곱해 반올림한다(정답본 105,341줄 중 96.60% 일치,\n"
        "                    // 종전 식 95.93%). 동점에서 갈린다: 10.5pt 160% → 628, 9pt 130% → 272.\n"
        "                    ((line_height_hwp / 4) as f64 * (ls_value - 100.0) / 100.0 + 0.5 + 1e-6).floor() as i32 * 4\n",
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
