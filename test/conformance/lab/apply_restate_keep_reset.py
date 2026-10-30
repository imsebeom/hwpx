"""개발용: 열 때 다시 재기(tac-restate-on-open)가 뒤 문단을 밀 때, 다음 쪽 맨 위 리셋 전까지만 같은 양을 민다. tac-restate-on-open 다음에 적용한다.

    python apply_restate_keep_reset.py [--revert]

근거(회귀 모음 「지능형 과학실 공모 계획」 c36): 18번 문단 4×3 표를 56936 → 56836(1.3px) 다시 쟀는데, 뒤 문단 밀기로 쓰던
recalculate_section_vpos 의 편집용 규칙(stale-reset-edit: 앞 흐름이 밀리면 저장 리셋을 흐름에 이어 붙임)이 그 구역의 한/글 쪽 나눔 자리를
모두 지워 8~10쪽 글이 12~52px 어긋났다(한/글과 2pt 넘는 줄 32 → 104). 리셋 전까지만 밀면 22. 에디터 저장본은 구역 누적 좌표라
리셋이 없어 종전과 같다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx restate-keep-reset]"

EDITS = [
    (
        "document_core/commands/document.rs",
        (
            "                seg.line_height = new_lh;\n"
            "                seg.text_height = new_lh;\n"
            "                doc.claude_shift_following_vpos(si, pi, old_end);\n"
            "                doc.recompose_paragraph(si, pi);\n"
        ),
        (
            "                let claude_delta = new_lh - seg.line_height;\n"
            "                seg.line_height = new_lh;\n"
            "                seg.text_height = new_lh;\n"
            f"                // {TAG} 뒤 문단은 다음 쪽 맨 위 리셋(저장 위치가 앞 문단 끝보다 작아지는 자리) 전까지만 같은 양을 민다. 편집용\n"
            "                // recalculate_section_vpos 는 앞 흐름이 밀리면 저장 리셋을 흐름에 이어 붙여(stale-reset-edit) 한/글 쪽 나눔 자리를\n"
            "                // 지웠다(c36: 1.3px 다시 잰 표 뒤 8~10쪽이 12~52px 어긋남)\n"
            "                {\n"
            "                    let paras = &mut doc.document.sections[si].paragraphs;\n"
            "                    let mut prev_end = old_end;\n"
            "                    for q in pi + 1..paras.len() {\n"
            "                        let Some(first) = paras[q].line_segs.first().map(|s| s.vertical_pos) else {\n"
            "                            continue;\n"
            "                        };\n"
            "                        if prev_end.is_some_and(|e| first < e) {\n"
            "                            break;\n"
            "                        }\n"
            "                        prev_end = crate::renderer::composer::paragraph_flow_end(&paras[q]);\n"
            "                        for s in &mut paras[q].line_segs {\n"
            "                            s.vertical_pos = s.vertical_pos.saturating_add(claude_delta);\n"
            "                        }\n"
            "                    }\n"
            "                }\n"
            "                doc.recompose_paragraph(si, pi);\n"
        ),
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
