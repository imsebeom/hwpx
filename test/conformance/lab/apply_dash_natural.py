"""개발용: 하이픈 3개 이상 묶음(Task #352 점선 채움)의 0.3em 상한은 글꼴 폭이 0.7em 을 넘을 때만 건다.

    python apply_dash_natural.py [--revert]

한/글 사본 실험(exp/make_charcal.py, read_charcal.py, 10pt 하이픈 8개 묶음): 함초롬바탕 5.517, 함초롬돋움 4.678, 맑은 고딕 4.112, 휴먼명조 4.986,
굴림 6.237, 바탕 6.237pt — 모두 그 글꼴의 「-」 폭이다(함초롬바탕 폭 표 550). 엔진은 묶음이면 글꼴과 상관없이 3.0pt(0.3em)로 줄였다.
Task #352 는 HY신명조 폭 표가 「-」 를 0.83em 으로 둔 문서 때문이라, 그런 큰 폭(0.7em 초과)에만 상한을 남긴다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx dash-natural]"

EDITS = [
    (
        "renderer/layout/text_measurement.rs",
        "    let dash_leader = is_dash_leader_run(chars, i);\n",
        f"    // {TAG} 한/글은 하이픈 묶음도 글꼴 폭으로 둔다(사본 실험 6종). 0.3em 상한은 폭 표가 0.7em 넘게 잡힌 글꼴(Task #352 HY신명조 0.83em)만\n"
        "    let dash_leader = is_dash_leader_run(chars, i) && base_width_raw > font_size * 0.7;\n",
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
