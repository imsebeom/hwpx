"""개발용: 글자의 언어 범주(어느 범주의 글꼴로 재는가)를 한/글 2024 실측대로 둔다(확인 뒤 editor/patches 로 옮긴다).

    python apply_lang_category.py [--revert]

근거(lab e7, e8): 일곱 범주 중 하나만 다른 글꼴로 바꾸고 한/글 PDF 글자 폭이 따라 바뀌는 범주를 쟀다. 한/글은
문맥(앞 글자)과 상관없이 글자마다 범주가 고정이다.
- 라틴: 빈칸, ASCII 문장 부호, Latin-1 기호(· × ÷ ° ± § 등), 따옴표 ‘ ’ ‚ “ ” „
- 기호: – — ― † ‡ • … ‰ ′ ″ ※ ‼, ™ ℃ (화살표, 수학 기호, 도형, 낫표는 rhwp 도 이미 기호)
rhwp 는 빈칸과 문장 부호를 「언어 중립」으로 두어 앞 글자의 범주(대개 한글)를 따랐다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx lang-category]"

EDITS = [
    (
        "renderer/style_resolver.rs",
        "    match cp {\n        // [#2070] ㆍ(아래아, U+318D)는 한컴이 USER 스크립트 폰트로 렌더한다.\n",
        "    match cp {\n"
        f"        // {TAG} 한/글 2024 실측(test/conformance/lab e7, e8): 문맥과 상관없이 고정 범주다.\n"
        "        // ASCII 문장 부호, Latin-1 기호, 따옴표 → 라틴. 빈칸(U+0020, U+00A0)도 한/글은 라틴이지만 앞 글자를 따르게\n"
        "        // 둔다(composer.rs is_lang_neutral) — 빈칸마다 글자 묶음이 쪼개지면 그리기와 커서 예측이 어긋나고,\n"
        "        // 「글꼴에 어울리는 빈칸」이 꺼진 대부분의 문서는 어느 글꼴이든 폭이 같다.\n"
        "        0x0021..=0x002F | 0x003A..=0x0040 | 0x005B..=0x0060 | 0x007B..=0x007E |\n"
        "        0x00A1..=0x00BF | 0x2018..=0x201F => 1,\n"
        "        // 대시, 단검표, 줄임표, 퍼밀, 프라임, 참고표, ™, ℃ → 기호\n"
        "        0x2013..=0x2015 | 0x2020..=0x203C | 0x2103 | 0x2122 => 5,\n"
        "        // [#2070] ㆍ(아래아, U+318D)는 한컴이 USER 스크립트 폰트로 렌더한다.\n",
    ),
    (
        "renderer/composer.rs",
        "    matches!(cp,\n"
        "        // 공백/제어문자\n"
        "        0x0000..=0x0020 |\n"
        "        // ASCII 구두점/기호 (영문자/숫자 제외)\n"
        "        0x0021..=0x002F | 0x003A..=0x0040 | 0x005B..=0x0060 | 0x007B..=0x007F |\n"
        "        // Latin-1 Supplement 구두점 (문자 제외)\n"
        "        0x00A0..=0x00BF\n"
        "    )\n",
        f"    // {TAG} 한/글은 문장 부호도 범주가 고정이다(라틴, detect_lang_category, test/conformance/lab e7, e8).\n"
        "    // 앞 글자를 따르는 것은 제어 문자와 빈칸뿐이다(빈칸을 두는 까닭은 detect_lang_category 주석).\n"
        "    matches!(cp, 0x0000..=0x0020 | 0x007F | 0x00A0)\n",
    ),
    (
        "document_core/commands/text_editing.rs",
        "        x += *positions.last()?;\n",
        f"        // {TAG} 배치 경로(paragraph_layout)는 지나간 글자 묶음을 반올림한 폭(estimate_text_width)으로 쌓는다.\n"
        "        // 문장 부호가 라틴 묶음으로 갈리며 묶음이 늘어 반올림 차이가 쌓이므로 같은 식으로 더한다(issue3137 시험).\n"
        "        let _ = positions.last()?;\n"
        "        x += crate::renderer::layout::estimate_text_width(&run.text, &style);\n",
    ),
    # upstream 시험 기대값을 실측 규칙에 맞춘다(문장 부호는 앞 글자를 따르지 않고 라틴)
    (
        "renderer/composer/tests.rs",
        "    assert!(is_lang_neutral(' '));\n"
        "    assert!(is_lang_neutral('.'));\n"
        "    assert!(is_lang_neutral(','));\n"
        "    assert!(is_lang_neutral('!'));\n"
        "    assert!(is_lang_neutral('('));\n",
        f"    // {TAG} 한/글은 문장 부호를 라틴 글꼴로 잰다(앞 글자를 따르지 않음, lab e7). 빈칸만 중립.\n"
        "    assert!(is_lang_neutral(' '));\n"
        "    assert!(!is_lang_neutral('.'));\n"
        "    assert!(!is_lang_neutral(','));\n"
        "    assert!(!is_lang_neutral('!'));\n"
        "    assert!(!is_lang_neutral('('));\n",
    ),
    (
        "renderer/composer/tests.rs",
        "    let composed = compose_paragraph(&para);\n"
        "    let run = &composed.lines[0].runs[0];\n"
        '    assert_eq!(run.text, text, "원문 IR은 바꾸지 않는다");\n'
        "    assert_eq!(\n"
        "        run.display_text.as_deref(),\n"
        '        Some("한글, 한메일, 한팩스, 한소프트, ᄒᆞᆫ겨울"),\n',
        "    let composed = compose_paragraph(&para);\n"
        f"    // {TAG} 쉼표가 라틴 묶음으로 갈리므로 묶음들을 이어 붙여 본다\n"
        "    let runs = &composed.lines[0].runs;\n"
        "    let joined: String = runs.iter().map(|run| run.text.as_str()).collect();\n"
        '    assert_eq!(joined, text, "원문 IR은 바꾸지 않는다");\n'
        "    let shown: String = runs\n"
        "        .iter()\n"
        "        .map(|run| run.display_text.as_deref().unwrap_or(run.text.as_str()))\n"
        "        .collect();\n"
        "    assert_eq!(\n"
        "        Some(shown.as_str()),\n"
        '        Some("한글, 한메일, 한팩스, 한소프트, ᄒᆞᆫ겨울"),\n',
    ),
    (
        "renderer/style_resolver.rs",
        "        // 공백, 구두점 등은 기본값(한국어=0)\n"
        "        assert_eq!(detect_lang_category(' '), 0);\n"
        "        assert_eq!(detect_lang_category('.'), 0);\n"
        "        assert_eq!(detect_lang_category(','), 0);\n",
        f"        // {TAG} 빈칸은 기본값(호출부가 앞 글자를 따름), 문장 부호는 라틴(한/글 2024 실측, lab e7)\n"
        "        assert_eq!(detect_lang_category(' '), 0);\n"
        "        assert_eq!(detect_lang_category('.'), 1);\n"
        "        assert_eq!(detect_lang_category(','), 1);\n",
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
