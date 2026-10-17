"""개발용: 실행 중 등록한 폭 표가 있는 글꼴은 한양중고딕, 한양신명조 빈칸 예외(0.55em, 0.40em)를 쓰지 않는다.

    python apply_runtime_no_space_overlay.py [--revert]

근거(lab e24): 한/글 2024 에서 한양중고딕, 한양신명조(type HFT)의 빈칸은 10, 12, 14, 40pt 모두, 「글꼴에 어울리는 빈칸」을
켜도 꺼도 0.5em 이다. 엔진은 다른 판의 PDF 에 맞춘 예외로 한양중고딕을 0.55em, 12pt 이상 한양신명조를 0.40em 으로 쟀다
(d317: 빈칸 17개에서 850 HU 넓어 두 글자 먼저 꺾었다). 등록 표가 없으면(HWP5 문서 등 에디터 밖) 종전대로 둔다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx runtime-no-space-overlay]"
REL = "renderer/layout/text_measurement.rs"

EDITS = [
    (
        REL,
        "    let (w, width_source) = if c == ' ' {\n"
        "        if let Some(width) = hancom_pdf_space_width(primary_name, font_size) {\n",
        f"    // {TAG} 실행 중 등록한 표(한/글 실측)가 있으면 한양 글꼴 빈칸 예외를 쓰지 않는다(lab e24: 한/글 2024 는 0.5em)\n"
        "    let (w, width_source) = if c == ' ' {\n"
        "        if let Some(width) = (mm.entry_index != usize::MAX)\n"
        "            .then(|| hancom_pdf_space_width(primary_name, font_size))\n"
        "            .flatten()\n"
        "        {\n",
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
