"""개발용: 선택 음영이 각주, 미주 번호 뒤에서 그 수만큼 앞으로 밀리던 문제를 고친다.

    python apply_sel_footnote_slot.py [--revert]

근거(2026-10-19 사용자 보고, 가이드북 4장 원고 _261019_12): 칸 안 문단(앞에 각주 셋)에서 끌어 고른 음영이 실제 고른 자리보다
세 글자 앞에 칠해졌다. 같은 오프셋에서 캐럿은 379.3px, 음영 시작은 347.0px(캐럿 87 자리)이고, 본문 각주 문단도 한 칸 밀린다.
caret-axis 음영은 캐럿 위치를 글자 축(logical_to_text_offset)으로 바꿔 렌더 조각 번호와 맞추는데, 렌더 조각 번호는 각주, 미주
번호 자리를 한 칸으로 센다(캐럿 계산도 각주 번호 노드를 캐럿 축 자리로 찾는다). 글자처럼 취급 표, 그림과 달리 각주, 미주는
빼지 않아야 해서, 바꾼 글자 위치에 앞선 각주, 미주 수를 더한다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx sel-footnote-slot]"

EDITS = [
    (
        "document_core/queries/cursor_nav.rs",
        "                                        let ta = crate::document_core::helpers::logical_to_text_offset(para, a).0;\n"
        "                                        let tb = crate::document_core::helpers::logical_to_text_offset(para, b).0;\n",
        f"                                        // {TAG} 렌더 조각 번호는 각주, 미주 번호 자리를 한 칸으로 센다 — 글자 축으로 바꾼 뒤 앞선 각주, 미주 수를 더한다\n"
        "                                        let claude_notes_before = |pos: usize| {\n"
        "                                            slots\n"
        "                                                .iter()\n"
        "                                                .enumerate()\n"
        "                                                .filter(|(ci, slot)| {\n"
        "                                                    slot.is_some_and(|s| s < pos)\n"
        "                                                        && matches!(\n"
        "                                                            para.controls.get(*ci),\n"
        "                                                            Some(crate::model::control::Control::Footnote(_))\n"
        "                                                                | Some(crate::model::control::Control::Endnote(_))\n"
        "                                                        )\n"
        "                                                })\n"
        "                                                .count()\n"
        "                                        };\n"
        "                                        let ta = crate::document_core::helpers::logical_to_text_offset(para, a).0 + claude_notes_before(a);\n"
        "                                        let tb = crate::document_core::helpers::logical_to_text_offset(para, b).0 + claude_notes_before(b);\n",
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
