"""개발용: 한컴 내장 글꼴(한양, 신명 계열, 명조)의 굵은 글자는 글자마다 0.05em 넓게 잰다(장평, 자간은 그 위에 곱함).

    python apply_hft_bold_extra.py [--revert]

근거(사본 실험 bh, bh2 — `exp/make_boldhft.py`, `exp/make_boldhft2.py`, PDF 글자 위치):
- PDF 에 T1 로 박히는 내장 글꼴 한양중고딕, 한양신명조, 한양견고딕, 신명 중고딕, 신명 태명조, 명조는 굵게면 한글, 라틴, 숫자, 부호 모두
  글자마다 전진 폭이 늘어난다. 늘어난 양 = 0.05 x 크기 x 장평 x (1 + 자간): 8pt 40, 10pt 50, 14pt 72, 20pt 100, 20pt 장평 90% 88,
  자간 -10% 88, 둘 다 81. 빈칸은 늘지 않는다. 설치된 TTF 로 그리는 휴먼명조, 다른 글꼴로 바뀐 글꼴은 늘지 않는다(bold-regular-width 그대로).
- 정답본 d317(한양중고딕): 같은 자간 -4% 에서 보통 「연구」 964, 굵은 「참고」 1013 = (1000 + 50) x 0.96 = 1008(PDF 배율 오차 안).
  엔진은 굵게도 보통 폭으로 재 줄마다 한 글자 더 담았다(「포함) 참|여」 대 한/글 「포함) |참여」).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx hft-bold-extra]"
F = "renderer/layout/text_measurement.rs"

EDITS = [
    (
        F,
        "    // [claude-hwpx dash-natural] 한/글은 하이픈 묶음도 글꼴 폭으로 둔다(사본 실험 6종).",
        f"    // {TAG} 한컴 내장 글꼴(한양, 신명 계열, 명조)의 굵은 글자는 0.05em 넓다(빈칸 제외, 장평과 자간은 그 위에 곱함 — lab 실험 bh, bh2)\n"
        "    let base_width_raw = base_width_raw + claude_hft_bold_extra_px(style, c, font_size);\n"
        "    // [claude-hwpx dash-natural] 한/글은 하이픈 묶음도 글꼴 폭으로 둔다(사본 실험 6종).",
    ),
    (
        F,
        "            .map(|width| f64::from(width) * font_size / f64::from(lookup.metric.em_size)),\n"
        "        _ => None,\n"
        "    }\n"
        "    .unwrap_or(decision.base_width_px);\n",
        "            .map(|width| f64::from(width) * font_size / f64::from(lookup.metric.em_size))\n"
        f"            // {TAG} 표를 다시 읽으므로 굵게 늘림도 다시 더한다(어림값 쪽은 decision 에 이미 들어 있다)\n"
        "            .map(|px| px + claude_hft_bold_extra_px(style, ch, font_size)),\n"
        "        _ => None,\n"
        "    }\n"
        "    .unwrap_or(decision.base_width_px);\n",
    ),
    (
        F,
        "/// [claude-hwpx hancom-quantum] 한/글이 줄을 나눌 때 쓰는 글자 폭(1/1800 인치 = HWPUNIT/4 단위).\n",
        f"/// {TAG} 한컴 내장 글꼴(PDF 에 T1 로 박히는 한양, 신명 계열, 명조)의 굵은 글자는 글자마다 0.05em 넓다(빈칸 제외).\n"
        "/// 설치된 TTF 로 그리는 글꼴(휴먼명조 등)과 다른 글꼴로 바뀌는 글꼴은 늘지 않는다(lab 실험 bh, bh2).\n"
        "fn claude_hft_bold_extra_px(style: &TextStyle, c: char, font_size: f64) -> f64 {\n"
        "    if style.bold\n"
        "        && !c.is_whitespace()\n"
        '        && (style.font_family.starts_with("한양")\n'
        '            || style.font_family.starts_with("신명")\n'
        '            || style.font_family == "명조")\n'
        "    {\n"
        "        font_size * 0.05\n"
        "    } else {\n"
        "        0.0\n"
        "    }\n"
        "}\n"
        "\n"
        "/// [claude-hwpx hancom-quantum] 한/글이 줄을 나눌 때 쓰는 글자 폭(1/1800 인치 = HWPUNIT/4 단위).\n",
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
            sys.exit(f"{rel}: 자리 {n}곳 — {find[:60]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel)


if __name__ == "__main__":
    main()
