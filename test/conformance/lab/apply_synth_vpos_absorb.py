"""개발용: 다시 조판한 문단의 합성 vpos 에서도 「표만 담은 자리 차지 표 호스트 바로 뒤 문단은 위 간격을 표 아래에 묻는다」(tbl-next-sb 와 짝).

    python apply_synth_vpos_absorb.py [--revert]

조판(typeset)은 tbl-next-sb 로 이미 맞다(d189 p7 734.8px = 한/글). 그리기는 합성 vpos 를 쓰는데 synth-vpos-spacing 이 위 간격을 늘 더해
d189 p6 이 52649(한/글 51524, 위 간격 1125 차)이고 그 뒤 1쪽 글이 모두 11.25pt 아래였다(exp/rendery.py). 정답본 근거는 tbl-next-sb 와 같다
(exp/harvest_tbl_nextsb.py 19/19, 빈 호스트 위 간격 24/24).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx synth-vpos-absorb]"

EDITS = [
    (
        "document_core/commands/document.rs",
        "                let mut claude_prev_after: i32 = 0;\n",
        "                let mut claude_prev_after: i32 = 0;\n"
        f"                // {TAG} 앞 문단이 표만 담은 문단 기준 자리 차지 표 호스트면 이 문단 위 간격은 표 아래에 묻힌다\n"
        "                let mut claude_prev_float_host = false;\n",
    ),
    (
        "document_core/commands/document.rs",
        "                        running_vpos += claude_prev_after\n"
        "                            + claude_hu(claude_style.map(|s| s.spacing_before).unwrap_or(0.0));\n",
        "                        running_vpos += claude_prev_after\n"
        "                            + if claude_prev_float_host {\n"
        "                                0\n"
        "                            } else {\n"
        "                                claude_hu(claude_style.map(|s| s.spacing_before).unwrap_or(0.0))\n"
        "                            };\n",
    ),
    (
        "document_core/commands/document.rs",
        "                    claude_prev_after = if claude_table_only_host || para.line_segs.is_empty() {\n",
        "                    claude_prev_float_host = claude_table_only_host\n"
        "                        && para.controls.iter().any(|c| {\n"
        "                            matches!(c, Control::Table(t)\n"
        "                                if !t.common.treat_as_char\n"
        "                                    && matches!(t.common.vert_rel_to, crate::model::shape::VertRelTo::Para))\n"
        "                        });\n"
        "                    claude_prev_after = if claude_table_only_host || para.line_segs.is_empty() {\n",
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
