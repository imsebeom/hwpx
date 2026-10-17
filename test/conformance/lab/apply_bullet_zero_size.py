"""개발용: 글머리표 글자 모양의 크기가 0 이면 문단 첫 글자 모양 크기로 글머리표 자리를 잡는다.

    python apply_bullet_zero_size.py [--revert]

근거(lab e31, 휴먼명조 14pt): 글머리표 글자 모양이 11pt 면 자리 = 11pt x 1.5(전각 칸 + 거리 50%), 0pt 면 14pt x 1.5 로 문단 글자 크기를
쓴다. 엔진의 bullet-advance 는 크기 0 이면 None 을 돌려 글머리표 자리를 아예 빼지 않았다(d302/d314 칸 248, 250: 한/글보다 1~3자 더 담음).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx bullet-zero-size]"

EDITS = [
    (
        "renderer/composer/line_breaking.rs",
        "    let font_size = styles\n        .char_styles\n        .get(char_style_id as usize)\n        .map(|style| style.font_size)\n        .filter(|size| *size > 0.0)?;\n    // 1/1800 인치(HWPUNIT/4) 단위\n    let em = font_size * 75.0 / 4.0;\n    let cell = if (bullet.bullet_char as u32) < 0x80 {",
        "    let font_size = styles\n        .char_styles\n        .get(char_style_id as usize)\n        .map(|style| style.font_size)\n        .filter(|size| *size > 0.0)\n"
        f"        // {TAG} 글머리표 글자 모양 크기가 0 이면 한/글은 문단 글자 크기로 자리를 잡는다(lab e31)\n"
        "        .or_else(|| {\n"
        "            para.char_shapes\n"
        "                .first()\n"
        "                .and_then(|shape| styles.char_styles.get(shape.char_shape_id as usize))\n"
        "                .map(|style| style.font_size)\n"
        "                .filter(|size| *size > 0.0)\n"
        "        })?;\n"
        "    // 1/1800 인치(HWPUNIT/4) 단위\n    let em = font_size * 75.0 / 4.0;\n    let cell = if (bullet.bullet_char as u32) < 0x80 {",
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
