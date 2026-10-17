"""개발용: 장평 100% 글자 폭도 4 HWPUNIT 단위로 내린다(반올림하지 않는다).

    python apply_quantum_floor.py [--revert]

근거(lab e12): 맑은 고딕 한글 「가」 30자를 「내림이면 30자, 반올림이면 29자」가 들어가는 폭에 넣으면, 크기 8종 × 장평
6종 중 판별 가능한 24경우 모두 한/글은 30자를 넣었다(내림). 엔진은 장평이 100% 일 때만 반올림해(예: 10.5pt 한글
262.5 단위 → 263 = 1052 HU, 한/글 1048) 칸 문단을 한 글자씩 일찍 끊었다(d089 등). 장평이 100% 가 아닐 때는 이미 내림이다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx quantum-floor]"

EDITS = [
    (
        "renderer/layout/text_measurement.rs",
        "    } else if plain {\n        (base_px * UNIT + 0.5 + EPS).floor()\n    } else {\n",
        "    } else if plain && (base_px - font_size).abs() < 1e-6 {\n"
        f"        // {TAG} 폭이 정확히 1em 인 전각 글자는 4 단위로 내린다(lab e12: 맑은 고딕 한글 10.5, 9.5, 11.5pt 모두 내림).\n"
        "        // 1em 이 아닌 글자(함초롬 계열 등)까지 내리면 코퍼스 일치율이 떨어져 그대로 둔다.\n"
        "        (base_px * UNIT + EPS).floor()\n"
        "    } else if plain {\n        (base_px * UNIT + 0.5 + EPS).floor()\n    } else {\n",
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
