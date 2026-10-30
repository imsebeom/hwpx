"""개발용: 글 없는 위아래 배치 표 문단의 저장 위치 0 을 쪽 넘김 신호로 보지 않는다.

    python apply_block_host_reset.py [--revert]

근거(d133 1쪽, d007, d165 3쪽): 표가 앞 쪽에 들어가면 한/글은 표를 그 쪽에 두고 품은 빈 줄만 다음 쪽 맨 위로 보낸다(줄 위치 0).
엔진은 이 0 을 보고 표까지 다음 쪽으로 넘겨 쪽수가 하나 늘었다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx block-host-reset]"

EDITS = [
    (
        "renderer/typeset.rs",
        (
            "                    let trigger = trigger\n"
            "                        && !omit_pushed_empty_page\n"
            "                        && !hangul2024_refit\n"
        ),
        (
            f"                    // {TAG} 위아래 배치 표가 든 문단이고 표가 남은 자리에 들어가면 쪽을 넘기지 않는다(품은 빈 줄만 다음 쪽)\n"
            "                    let claude_block_host_fits = para.controls.iter().any(|c| matches!(c, Control::Table(t) if !t.common.treat_as_char\n"
            "                            && t.common.text_wrap == crate::model::shape::TextWrap::TopAndBottom\n"
            "                            && st.current_height + crate::renderer::hwpunit_to_px(t.common.height as i32, self.dpi)\n"
            "                                <= st.available_height()));\n"
            "                    let trigger = trigger\n"
            "                        && !claude_block_host_fits\n"
            "                        && !omit_pushed_empty_page\n"
            "                        && !hangul2024_refit\n"
        ),
    ),
]


def main():
    revert = "--revert" in sys.argv
    for rel, find, repl in EDITS:
        p = SRC / rel
        raw = p.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        s = raw.replace("\r\n", "\n")
        a, b = (repl, find) if revert else (find, repl)
        assert s.count(a) == 1, (rel, a[:70], s.count(a))
        p.write_bytes(s.replace(a, b).replace("\n", nl).encode("utf-8"))
    print("되돌림" if revert else "적용")


if __name__ == "__main__":
    main()
