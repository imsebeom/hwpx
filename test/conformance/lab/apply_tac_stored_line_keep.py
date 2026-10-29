"""개발용: 저장 줄 배치가 있는 HWPX 문단의 줄 안 글자처럼 취급 표는 폭 어림으로 다음 줄로 넘기지 않는다(저장 나눔이 권위).

    python apply_tac_stored_line_keep.py [--revert]

근거(2026-10-29 결과보고서 21:27 판 40쪽, 189번 소제목): 「    3) AI 동아리 연계 운영」 + 빈칸 43개 + 꼬리표 표(9600)가 저장 줄 하나다.
한/글은 표를 그 줄 오른쪽(글+빈칸 끝 476.5px 뒤, 줄 폭 604.7px 에 0.2px 남김)에 그린다. 엔진 그리기는 글 폭을 estimate_text_width 로 따로
어림해 「글 + 표 > 줄 폭」이라 표를 다음 줄 맨 앞에 그렸고, 그 아래 본문이 43px 밀렸다(조판은 저장 줄대로 한 줄이라 쪽수는 같았다).
저장 나눔 인덱스가 표 위치 이하로 남아 있을 때만 넘긴다(#6180 의 글자 판정과 같은 원리).
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx tac-stored-line-keep]"

EDITS = [
    (
        "renderer/layout/paragraph_layout.rs",
        (
            "                let table_wrapped = should_wrap_middle_anchored_table(\n"
            "                    control_positions.get(*ctrl_idx).copied(),\n"
            "                    text_chars.len(),\n"
            "                    inline_x - line_start_x,\n"
            "                    table_footprint,\n"
            "                    right_margin - line_start_x,\n"
            "                );\n"
        ),
        (
            f"                // {TAG} 저장 줄 배치가 있는 HWPX 문단은 저장 나눔이 권위다 — 표 위치 이하의 나눔이 남아 있을 때만 넘긴다\n"
            "                // (결과보고서 189번: 글 + 빈칸 43개 + 표가 저장 한 줄인데 폭 어림으로 표를 다음 줄로 넘겨 본문이 43px 밀렸다)\n"
            "                let claude_stored_lines = self.profile.get().hwpx_container()\n"
            "                    && !para.line_segs.is_empty()\n"
            "                    && para.line_segs.iter().all(|s| s.tag & 0x8000_0000 == 0);\n"
            "                let table_wrapped = if claude_stored_lines {\n"
            "                    let pos = control_positions.get(*ctrl_idx).copied().unwrap_or(0);\n"
            "                    let wrap = next_break < line_break_char_indices.len()\n"
            "                        && line_break_char_indices[next_break] <= pos\n"
            "                        && inline_x > line_start_x + 1.0;\n"
            "                    if wrap {\n"
            "                        next_break += 1;\n"
            "                    }\n"
            "                    wrap\n"
            "                } else {\n"
            "                    should_wrap_middle_anchored_table(\n"
            "                        control_positions.get(*ctrl_idx).copied(),\n"
            "                        text_chars.len(),\n"
            "                        inline_x - line_start_x,\n"
            "                        table_footprint,\n"
            "                        right_margin - line_start_x,\n"
            "                    )\n"
            "                };\n"
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
