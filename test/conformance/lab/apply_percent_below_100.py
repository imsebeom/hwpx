"""개발용: 100% 미만 비율 줄 간격을 한/글처럼 계산한다(4 단위 반올림, HWPX 의 0% 는 간격 = -줄 높이).

    python apply_percent_below_100.py [--revert]

근거(2026-10-18 정답본 한/글 줄 기록, 100% 미만 비율 문단 수백 줄):
- 간격 = round(줄 높이 x (비율 - 100)% / 4) x 4 (반올림은 0 에서 먼 쪽). 예: 900 x -55% = -495 -> -496, 1800 x -75% = -1350 -> -1352,
  1300 x -70% = -910 -> -912, 1100 x -95% = -1045 -> -1044. 엔진은 4 단위 반올림 없이 -495 를 그대로 썼다.
- 0% 는 간격 = -줄 높이(24줄 모두, d201 p74 1100 -> -1100). 엔진은 0 을 「속성 없음」으로 보고 간격 0 으로 둬, d201 5쪽이 1100 내려갔다.
  HWPX 581개 문서의 문단 모양 32,618개 가운데 줄 간격 요소가 없는 것은 0개, 명시적 0% 는 13개라 HWPX 의 0 은 명시값으로 본다
  (해석 단계에서 아주 작은 양수로 바꿔 넘긴다. HWP5 의 0 은 종전대로 결손으로 둔다).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx percent-below-100]"

EDITS = [
    (
        "renderer/composer/line_breaking.rs",
        "                } else {\n"
        "                    spacing.round() as i32\n"
        "                }\n",
        "                } else {\n"
        f"                    // {TAG} 100% 미만도 4 단위로 반올림(0 에서 먼 쪽): 900 x -55% = -495 -> -496(정답본 수백 줄)\n"
        "                    ((spacing / 4.0).round() as i32) * 4\n"
        "                }\n",
    ),
    (
        "renderer/style_resolver.rs",
        "        .map(|ps| resolve_single_para_style(ps, &doc_info.tab_defs, dpi, is_hwp3_variant))\n",
        "        .map(|ps| {\n"
        "            let mut style = resolve_single_para_style(ps, &doc_info.tab_defs, dpi, is_hwp3_variant);\n"
        f"            // {TAG} HWPX 의 비율 0% 는 명시값이다(간격 = -줄 높이, 정답본 24줄). 줄 간격 계산은 0 을 결손으로 보니 아주 작은 양수로 넘긴다\n"
        "            if doc_info.hwpx_head_tail.is_some()\n"
        "                && matches!(ps.line_spacing_type, LineSpacingType::Percent)\n"
        "                && ps.line_spacing == 0\n"
        "            {\n"
        "                style.line_spacing = 1e-6;\n"
        "            }\n"
        "            style\n"
        "        })\n",
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
