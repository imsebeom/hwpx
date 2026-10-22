"""개발용: 하이픈 점 「‧」(U+2027)도 「·」 처럼 줄 머리에 오지 않는다.

    python apply_hyphen_point_kinsoku.py [--revert]

근거(새 정답본): 한글 뒤 「‧」 바로 앞에서 한/글이 꺾은 곳 70곳 중 0, 「‧」 뒤 한글 앞에서는 72곳 중 3(d017 「창의적‧|비판적」,
d264 「발굴‧|개선하고」, d321 「교수‧|학습」). 엔진은 이 셋을 「창의적|‧비판적」 처럼 ‧ 를 다음 줄 머리에 두었다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx hyphen-point-kinsoku]"

EDITS = [
    (
        "renderer/composer/line_breaking.rs",
        "            | '\\u{00B7}'\n",
        "            | '\\u{00B7}'\n"
        f"            // {TAG} 하이픈 점 ‧ 도 줄 머리에 오지 않는다(새 정답본 한글 뒤 70곳 중 0)\n"
        "            | '\\u{2027}'\n",
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
