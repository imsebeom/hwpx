"""개발용: 표 하나만 담은 빈 문단(위아래 배치, 줄 배치 없음)은 흐름에 문단 아래 간격을 더하지 않는다.

    python apply_empty_host_no_after.py [--revert]

근거(정답본 집계 harvest_tblnext.py): 글자처럼 취급이 아닌 위아래 배치 표만 담은 본문 문단에서 문단 아래 간격이 있는 15건 모두
한/글은 그 간격을 더하지 않았다(다음 문단 vertpos - 이 문단 vertpos = 표 높이 + 바깥 여백). 엔진은 오프셋과 바깥 여백이 0 이면
문단 아래 간격이 섞인 형식 높이(table_total)를 더해 d089 의 표 문단마다 500 이 남았다.
선언 높이(hp:sz)로 바꾸면 안 된다: 생성기(md2hwpx)가 적는 2,400 x 행 수는 실제보다 작아 쪽이 줄었다(0043_AI_Ethics_Guide 10 → 9쪽,
한/글 10쪽). 그래서 잰 높이에서 문단 아래 간격만 뺀다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx empty-host-no-after]"

EDITS = [
    (
        "renderer/typeset.rs",
        "            } else {\n                st.current_height += pre_height + table_total_height;\n            }\n        }\n        // [#2243 진단] TAC 표 라인 회계 분해",
        "            } else {\n"
        f"                // {TAG} 줄 배치 없는 빈 문단의 위아래 배치 표 하나는 잰 높이에서 문단 아래 간격을 뺀다. 한/글은 표만 담은\n"
        "                // 문단의 아래 간격을 더하지 않는다(정답본 15건 중 15건). 선언 높이는 생성기 값이 낡을 수 있어 쓰지 않는다\n"
        "                let claude_empty_host = is_para_topbottom_float(&table.common)\n"
        "                    && !para_has_non_whitespace_text(para)\n"
        "                    && crate::renderer::para_has_no_stored_line_segs(para)\n"
        "                    && para.controls.iter().filter(|control| matches!(control, Control::Table(_))).count() == 1;\n"
        "                let claude_after = if claude_empty_host { fmt.spacing_after.min(table_total_height).max(0.0) } else { 0.0 };\n"
        "                st.current_height += pre_height + table_total_height - claude_after;\n"
        "            }\n        }\n        // [#2243 진단] TAC 표 라인 회계 분해",
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
