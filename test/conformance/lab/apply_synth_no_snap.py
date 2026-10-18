"""개발용: 엔진이 만든 줄(저장 줄 배치가 아닌 줄) 문단에서는 vpos 로 누적 높이를 되맞추지 않는다.

    python apply_synth_no_snap.py [--revert]

근거: 2026-10-18 사용자 보고 「사람이 고치면 괜찮은데 에디터(Claude 도구)가 고치면 높이, 쪽이 어긋난다」.
editor/tests/edit_consistency.mjs 로 도구 28종을 「편집 직후 조판」 대 「같은 결과를 처음부터 조판」으로 맞대니 6종이 달랐다
(format_text, table_caption, page_setup, create_table, clone_table, set_list). 편집 경로는 줄을 새로 만든 뒤 vpos 사슬을
다시 잇지 않아(예: reflow_body_paragraphs_in_section 은 모든 문단 vpos 를 0 으로 둔다) 스냅이 그 값으로 쪽을 틀었다.
예전에 같은 처방이 쪽수 지표를 0.3%p 떨어뜨렸는데 원인은 열기 경로 사슬의 문단 간격 누락이었고(synth-vpos-spacing 으로 고침),
이제는 정답본 채점이 쪽수 93.6 → 93.9%(d327), 문단 쪽 그대로다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx synth-no-snap]"

EDITS = [
    (
        "renderer/typeset.rs",
        "            st.vpos_ladder_dirty = false;\n        }\n        let mut hc = HeightCursor {\n            dpi: self.dpi,\n            col_area_y: 0.0,\n",
        "            st.vpos_ladder_dirty = false;\n        }\n"
        f"        // {TAG} 엔진이 만든 줄(저장 줄 배치가 아닌 줄)의 vpos 로는 누적 높이를 되맞추지 않는다. 편집 경로\n"
        "        // (쪽 설정, 표 넣기, 캡션 등)는 줄을 새로 만든 뒤 vpos 사슬을 다시 잇지 않아 0 이나 낡은 값이 남고, 스냅이 그 값으로 쪽을\n"
        "        // 틀었다(2026-10-18 사용자 보고 「에디터가 고치면 쪽이 어긋난다」, editor/tests/edit_consistency.mjs). 열기 경로의 사슬에\n"
        "        // 문단 간격을 넣은 뒤(synth-vpos-spacing)에는 정답본 채점도 쪽수 93.6 → 93.9%, 문단 쪽 그대로\n"
        "        if paragraphs.get(para_idx).and_then(|p| p.line_segs.first()).is_some_and(|s| {\n"
        "                s.tag & crate::model::paragraph::LineSeg::TAG_IMPLEMENTATION_PROPERTY != 0\n"
        "            })\n"
        "        {\n"
        "            return;\n"
        "        }\n"
        "        let mut hc = HeightCursor {\n            dpi: self.dpi,\n            col_area_y: 0.0,\n",
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
