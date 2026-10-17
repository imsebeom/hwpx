"""개발용: 느낌표(!)의 폭을 글꼴과 상관없이 글자 크기의 절반으로 잰다.

    python apply_exclam_half.py [--revert]

근거(lab e15, e16): 한/글 2024 PDF 에서 「!」 의 전진 폭은 함초롬바탕(글리프 0.320em), 맑은 고딕 모두 40pt 에서 20.03pt(0.5em)다.
뒤에 한글, 라틴, 빈칸, 「!」 무엇이 와도 같고, PDF 에는 글리프 뒤에 빈칸 글자를 하나 더 찍어 그 폭을 채운다.
「?」, 「.」 는 글꼴 폭 그대로다. 엔진은 글꼴 폭(0.32em 안팎)으로 쟀다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx exclam-half]"

EDITS = [
    (
        "renderer/layout/text_measurement.rs",
        "    let dash_leader = is_dash_leader_run(chars, i);\n",
        f"    // {TAG} 한/글은 「!」 의 폭을 글꼴과 상관없이 글자 크기의 절반으로 둔다(test/conformance/lab e15, e16).\n"
        "    let (base_width_raw, width_source) = if c == '!' {\n"
        '        (font_size * 0.5, "hancomExclamHalf")\n'
        "    } else {\n"
        "        (base_width_raw, width_source)\n"
        "    };\n"
        "    let dash_leader = is_dash_leader_run(chars, i);\n",
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
