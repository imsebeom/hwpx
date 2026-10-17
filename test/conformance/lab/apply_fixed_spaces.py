"""개발용: 고정폭 빈칸(fwSpace, U+2007)은 0.25em, 묶음 빈칸(nbSpace, U+00A0)은 0.5em 으로 잰다.

    python apply_fixed_spaces.py [--revert]

근거(lab e26, 40pt): 한/글 2024 의 고정폭 빈칸은 함초롬바탕, 맑은 고딕, 휴먼명조, 한양중고딕 모두 「글꼴에 어울리는 빈칸」을
켜도 꺼도 0.25em, 묶음 빈칸은 늘 0.5em 이다(켜면 보통 빈칸은 글꼴 폭이 되는데 묶음 빈칸은 그대로 0.5em).
엔진은 고정폭 빈칸을 0.5em, 묶음 빈칸을 글꼴 표의 U+00A0 이나 어림값으로 쟀다(불일치 문단 35건에 고정폭 빈칸).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx fixed-spaces]"

EDITS = [
    (
        "renderer/layout/text_measurement.rs",
        "    if c == '\\u{2007}' {\n        let base_width_px = font_size * 0.5;\n",
        f"    // {TAG} 한/글 2024: 고정폭 빈칸(fwSpace → U+2007)은 0.25em, 묶음 빈칸(nbSpace → U+00A0)은 0.5em(lab e26, 글꼴과 설정 무관)\n"
        "    if c == '\\u{2007}' || c == '\\u{00A0}' {\n"
        "        let base_width_px = font_size * if c == '\\u{2007}' { 0.25 } else { 0.5 };\n",
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
            sys.exit(f"{rel}: 자리 {n}곳 — {find[:50]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel)


if __name__ == "__main__":
    main()
