"""개발용: 엔진이 만든 줄(저장 줄 배치가 아닌 줄)의 첫 vpos 0 은 「한/글이 여기서 쪽을 끊었다」는 신호로 읽지 않는다.

    python apply_synth_no_reset.py [--revert]

근거: editor/tests/edit_consistency.mjs — format_text(p9 글자 크기) 뒤 편집 직후 조판은 p9 를 2쪽에 두고, 같은 결과를 처음부터
조판하면 1쪽에 둔다. 글자 서식 경로는 줄을 지우고 다시 만들어 첫 vpos 가 0 이 되고, 조판기의 저장 vpos 리셋 강제 분할(Task #321,
cv == 0 && pv > 5000)이 그 0 을 쪽 나눔으로 읽었다. 문서를 열 때 엔진이 만든 줄은 사슬로 이어 0 이 생기지 않으니(document.rs)
엔진이 만든 줄의 0 은 언제나 편집의 흔적이다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx synth-no-reset]"

EDITS = [
    (
        "renderer/typeset.rs",
        "                            || near_page_top_reset\n"
        "                            || native_near_top_reset\n"
        "                            || stored_top_collision_reset\n"
        "                    };\n",
        "                            || near_page_top_reset\n"
        "                            || native_near_top_reset\n"
        "                            || stored_top_collision_reset\n"
        "                    };\n"
        f"                    // {TAG} 엔진이 만든 줄의 vpos 는 저장 쪽 경계가 아니다. 편집 도구가 줄을 다시 만들면 첫 vpos 가 0 이 되어\n"
        "                    // 여기서 쪽이 끊겼다(2026-10-18 「에디터가 고치면 쪽이 어긋난다」, editor/tests/edit_consistency.mjs format_text)\n"
        "                    let trigger = trigger && !para.line_segs.first().is_some_and(is_synthetic_line_seg);\n",
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
