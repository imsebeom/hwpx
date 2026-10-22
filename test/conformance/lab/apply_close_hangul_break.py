"""개발용: 글자 단위 문단은 닫는 부호(] ) } 」 』 ’ ” ' / , -) 바로 뒤 한글 앞에서도 꺾는다.

    python apply_close_hangul_break.py [--revert]

근거(새 정답본 327문서, 글자 단위 문단, 조판 부호 없는 문단): 「부호 -> 한글」 경계에서 한/글이 꺾은 수 — ) 15/650, - 6/140,
' 5/222, / 4/84, , 4/13, ’ 2/177, ” 2/107, ] 1/127, 」 1/99. 여는 부호 ( [ 「 “ ‘ 와 . % " 뒤는 0 번(각 82~1,734곳).
엔진은 이 부호가 한글 뒤에 붙으면(「등)」, 줄 머리 금칙 덩이) 그 뒤를 꺾지만, 숫자나 라틴 뒤에 붙으면(「[자료 2]|는」, 「3」|을」)
꺾을 자리가 없어 앞 빈칸까지 물러났다(d031, d032). latin-hangul-break 의 앞 글자 목록을 넓힌다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx close-hangul-break]"

EDITS = [
    (
        "renderer/composer/line_breaking.rs",
        "        && (text_chars[idx - 1].is_ascii_alphanumeric() || text_chars[idx - 1] == '\\u{2022}')\n}\n",
        "        && (text_chars[idx - 1].is_ascii_alphanumeric()\n"
        "            || text_chars[idx - 1] == '\\u{2022}'\n"
        f"            // {TAG} 닫는 부호, 빗금, 쉼표, 붙임표 뒤 한글 앞도(새 정답본 「2]|는」, 「3」|을」, 「AI,|기반」)\n"
        "            || matches!(\n"
        "                text_chars[idx - 1],\n"
        "                ']' | ')' | '}' | '\\'' | '/' | ',' | '-' | '\\u{300D}' | '\\u{300F}' | '\\u{2019}' | '\\u{201D}'\n"
        "            ))\n"
        "}\n",
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
