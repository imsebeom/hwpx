"""개발용: 줄 배치를 다시 만든 문단의 vpos 사슬에 문단 위아래 간격을 넣는다.

    python apply_synth_vpos_spacing.py [--revert]

근거: 한/글이 저장한 줄 배치의 vertpos 는 「앞 문단 끝 + 앞 문단 아래 간격 + 이 문단 위 간격」에서 시작한다(d089 p16→p17
1,978 = 1,050 + 428 + 500). 엔진은 줄 배치가 없는 문서를 읽을 때 문단 vpos 를 줄 높이와 줄 간격만 이어 붙여(1,478) 만들고,
조판은 둘째 쪽부터 이 값에 맞춰(snap) 커서를 끌어당겨 문단마다 간격만큼 덜 내려갔다(d089 둘째 쪽 문단마다 300).
표만 담은 문단(위아래 배치)의 아래 간격은 한/글이 더하지 않으므로(harvest_tblnext.py, 15건 중 15건) 넣지 않는다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx synth-vpos-spacing]"
DOC = "document_core/commands/document.rs"

EDITS = [
    (
        DOC,
        "                let mut prev_stored_last_vpos: i32 = 0;\n",
        "                let mut prev_stored_last_vpos: i32 = 0;\n"
        f"                // {TAG} 앞 문단의 아래 간격(HWPUNIT). 다시 조판한 문단 앞에 「앞 아래 + 이 문단 위」 간격을 둔다\n"
        "                let mut claude_prev_after: i32 = 0;\n",
    ),
    (
        DOC,
        "                    // 문단의 첫 LINE_SEG vpos를 running_vpos로 갱신\n",
        f"                    // {TAG} 한/글 vertpos 는 문단 위아래 간격을 품는다. 다시 조판한 문단만(저장 줄 배치는 그대로)\n"
        "                    let claude_style = styles.para_styles.get(para.para_shape_id as usize);\n"
        "                    let claude_hu = |px: f64| (px * 7200.0 / dpi).round() as i32;\n"
        "                    if was_reflowed && !para.line_segs.is_empty() {\n"
        "                        running_vpos += claude_prev_after\n"
        "                            + claude_hu(claude_style.map(|s| s.spacing_before).unwrap_or(0.0));\n"
        "                    }\n"
        "                    // 문단의 첫 LINE_SEG vpos를 running_vpos로 갱신\n",
    ),
    (
        DOC,
        "                    running_vpos = inner_vpos;\n                    if let Some(v) = original_last_vpos {\n",
        "                    running_vpos = inner_vpos;\n"
        f"                    // {TAG} 표만 담은 문단(위아래 배치)의 아래 간격은 한/글이 더하지 않는다\n"
        "                    let claude_table_only_host = para.text.trim().is_empty()\n"
        "                        && para.controls.iter().any(|c| {\n"
        "                            matches!(c, Control::Table(t)\n"
        "                                if !t.common.treat_as_char\n"
        "                                    && matches!(t.common.text_wrap, crate::model::shape::TextWrap::TopAndBottom))\n"
        "                        });\n"
        "                    claude_prev_after = if claude_table_only_host || para.line_segs.is_empty() {\n"
        "                        0\n"
        "                    } else {\n"
        "                        claude_hu(claude_style.map(|s| s.spacing_after).unwrap_or(0.0))\n"
        "                    };\n"
        "                    if let Some(v) = original_last_vpos {\n",
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
