"""개발용: 한컴 내장(HFT) 글꼴의 기호 폭을 한/글 2024 실측값으로 둔다(확인 뒤 editor/patches 로 옮긴다).

    python apply_hft_symbols.py [--revert]

근거(lab e2, e5): 휴먼명조는 글꼴 파일이 없어(한/글 내장) 엔진이 HY신명조 표와 좁은 기호 어림을 쓰는데, 한/글 2024 PDF
글자 위치로 잰 폭은 `·`, `…`, `“`, `”`, `‘`, `’` 가 전각(1em), `—` 가 0.879em 이다(10pt, 한글 사이 문맥 12회 중앙값).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx hft-symbol-widths]"

EDITS = [
    (
        "renderer/layout/text_measurement.rs",
        "pub(crate) fn char_width_decision<'a>(\n",
        f"/// {TAG} 한/글 2024 에서 잰 한컴 내장(HFT) 글꼴의 기호 폭(em). 글꼴 파일이 없어 내장 표와 어림이 틀리던 것\n"
        "/// (test/conformance/lab e5: 한/글 PDF 글자 위치, 10pt 한글 사이 12회 중앙값).\n"
        "fn claude_hft_symbol_em(font_family: &str, c: char) -> Option<f64> {\n"
        "    let primary = font_family\n"
        "        .split(',')\n"
        "        .next()\n"
        '        .unwrap_or("")\n'
        "        .trim()\n"
        "        .trim_matches('\\'')\n"
        "        .trim_matches('\"');\n"
        "    match (primary, c) {\n"
        "        (\"휴먼명조\", '\\u{00B7}' | '\\u{2026}' | '\\u{201C}' | '\\u{201D}' | '\\u{2018}' | '\\u{2019}') => Some(1.0),\n"
        "        (\"휴먼명조\", '\\u{2014}') => Some(0.879),\n"
        "        _ => None,\n"
        "    }\n"
        "}\n"
        "\n"
        "pub(crate) fn char_width_decision<'a>(\n",
    ),
    (
        "renderer/layout/text_measurement.rs",
        "    let dash_leader = is_dash_leader_run(chars, i);\n",
        f"    // {TAG} 실측 기호 폭이 있으면 그것을 쓴다\n"
        "    let (base_width_raw, width_source) = match claude_hft_symbol_em(&style.font_family, c) {\n"
        '        Some(em) => (font_size * em, "hftMeasuredSymbol"),\n'
        "        None => (base_width_raw, width_source),\n"
        "    };\n"
        "    let dash_leader = is_dash_leader_run(chars, i);\n",
    ),
    (
        "renderer/layout/text_measurement.rs",
        "        // 비례폰트의 .notdef 위장 전각(≈20px) 이 아니라 narrow(0.3em ≈ 6px) 여야 함.\n"
        "        assert!(\n"
        "            dot_advance <= style.font_size * 0.4,\n",
        f"        // {TAG} 한/글 2024 는 휴먼명조 `·` 를 전각으로 조판한다(lab e5). upstream 의 narrow 기대는 옛 한/글 PDF 기준.\n"
        "        assert!(\n"
        "            dot_advance >= style.font_size * 0.95,\n",
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
