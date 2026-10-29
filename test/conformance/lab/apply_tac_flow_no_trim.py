"""개발용: HWPX 에서 다음 문단이 글자처럼 취급 + flowWithText 표(TAC 흐름 경로)면 앞 글 문단은 간격을 줄여 전진하지 않는다.

    python apply_tac_flow_no_trim.py [--revert]

근거(2026-10-29 결과보고서 21:27 판, 한/글 재저장본 43쪽): 소제목 「2) 전체 결과」(228), 「3) 영역별 …」(232)는 줄 1100 + 간격 660 으로
다음 표 문단이 1810(24.1px) 아래에서 시작한다. 엔진은 소제목을 맞춤 높이 14.7px 만큼만 전진하고 나머지는 다음 문단의 저장 위치
스냅이 되찾는다고 보는데(spacing_trim_restorable: 다음 문단에 개체가 있으면 복원 가능), TAC 흐름 표 문단 경로는 스냅하지 않아 간격이
사라졌다. 233번 표가 한/글보다 10.6px 위에서 시작해 43쪽에 겨우 들어가(895.5 ≤ 895.8) 한/글 49쪽, 엔진 48쪽이 됐다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx tac-flow-no-trim]"

EDITS = [
    (
        "renderer/typeset.rs",
        (
            "                st.vpos_ladder_dirty\n"
            "                    || !spacing_trim_restorable(paragraphs, para_idx)\n"
            "                    || (st.vpos_page_base.is_none() && st.vpos_lazy_base.is_none()),\n"
        ),
        (
            "                st.vpos_ladder_dirty\n"
            "                    || !spacing_trim_restorable(paragraphs, para_idx)\n"
            "                    || (st.vpos_page_base.is_none() && st.vpos_lazy_base.is_none())\n"
            f"                    // {TAG} 다음 문단이 TAC 흐름 표면 그 경로는 저장 위치로 스냅하지 않아 줄인 간격을 되찾지 못한다(결과보고서 228, 232)\n"
            "                    || (st.profile.hwpx_container()\n"
            "                        && paragraphs.get(para_idx + 1).is_some_and(|next| {\n"
            "                            next.controls.iter().any(|c| {\n"
            "                                matches!(c, Control::Table(t) if t.common.treat_as_char && t.common.flow_with_text)\n"
            "                            })\n"
            "                        })),\n"
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
