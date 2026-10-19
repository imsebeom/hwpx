"""개발용: 여백을 뺀 줄 폭이 1440HU(0.2인치)보다 좁으면 한/글처럼 문단 여백을 버린다.

    python apply_min_line_margin.py [--revert]

새 정답본의 칸 문단(왼쪽, 오른쪽 여백만 있고 들여쓰기 없음) 가운데 「칸 안쪽 폭 − 여백 < 1440」 인 줄 211개가 모두 horzpos 0, 줄 폭 1440
이다(칸 안쪽 폭 1427 이든 1712 든). 엔진은 칸 안쪽 폭에만 1440 하한(HANGUL_MIN_CELL_LINE_WIDTH_HWPUNIT)을 두고 여백을 뺀 뒤에는 하한이
없어, d034 차례 표의 쪽 번호 칸(폭 2447, 칸 여백 510x2, 문단 여백 500 + 200)에서 「10」 을 줄 폭 727 에 넣지 못해 「1」 뒤에서 꺾었다(칸 8개,
행이 두 줄 높이로 커져 뒤 글이 21.9px 아래). narrow-margin-ignore 의 「남는 폭 < 줄 폭의 25%」(d322 사본 실험) 에 「남는 폭 < 1440HU」 를
더한다. 여백을 버리면 칸 안쪽 폭(이미 1440 하한)이 줄 폭이 된다. 1440HU 는 엔진 기본 dpi 96 에서 19.2px.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx min-line-margin]"

EDITS = [
    (
        "renderer/style_resolver.rs",
        "    used > 0.0 && full_px > 0.0 && full_px - used < full_px * 0.25\n}\n",
        f"    // {TAG} 여백을 뺀 줄 폭이 1440HU(dpi 96 에서 19.2px)보다 좁아도 무시한다(새 정답본 칸 줄 211/211: horzpos 0, 폭 1440)\n"
        "    used > 0.0\n"
        "        && full_px > 0.0\n"
        "        && (full_px - used < full_px * 0.25\n"
        "            || full_px - used < 1440.0 / 7200.0 * crate::renderer::DEFAULT_DPI)\n"
        "}\n",
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
