"""개발용: 선택 음영과 줄 시작에서 각주, 미주를 캐럿 칸으로 세지 않는다(sel-footnote-slot 대체).

    python apply_sel_note_text_axis.py [--revert]

근거(2026-10-19 사용자 보고, 가이드북 3장 _261019_19 4쪽 「백엔드 코드가 작동하려면」 문단, 각주 11):
에디터의 본문, 칸 캐럿 축에서 각주는 칸이 아니다 — 문단 길이(getParagraphLength)가 글자 수 264 이고, 캐럿 193 에 글을
넣으면 「,」 뒤(글자 193)에 들어가고, 오른쪽 키는 192 → 193 → 194 로 한 칸씩 가며, 렌더 글자 조각 번호도 각주를 세지 않는다
(「(Hosting)」 183~191 다음 「, 」 192). 그런데 선택 음영은 caret_control_slots 로 각주를 캐럿 칸으로 세어
① 각주 뒤 글자 하나(「,」)를 각주 상자 조각으로 바꿔 칠하지 않았고, ② 줄 시작(utf16_pos_to_caret_idx)을 각주 수만큼 밀어
다음 줄 첫 글자까지 앞줄 범위에 넣어 각주 뒤 조각이 줄 처음부터 그려졌다(사각형 107.8 → 416.4).
10-19 의 sel-footnote-slot(앞선 각주 수를 더함)은 ①②를 남긴 채 글자 위치만 상쇄했다. 글자처럼 취급 표, 그림, 수식은
종전대로 캐럿 칸이다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx sel-note-text-axis]"

EDITS = [
    (
        "document_core/helpers.rs",
        "pub(crate) fn caret_control_slots(para: &Paragraph) -> Vec<Option<usize>> {\n",
        f"/// {TAG} 선택 음영용 캐럿 칸 — caret_control_slots 와 같되 각주, 미주는 칸이 아니다(에디터 캐럿 축은 각주를 세지 않는다).\n"
        "pub(crate) fn claude_caret_slots_no_notes(para: &Paragraph) -> Vec<Option<usize>> {\n"
        "    let mut slots = vec![None; para.controls.len()];\n"
        "    let mut c = 0usize;\n"
        "    for (ci, is_caret, _) in caret_axis_items(para) {\n"
        "        let is_caret = is_caret\n"
        "            && !ci.is_some_and(|ci| matches!(para.controls[ci], Control::Footnote(_) | Control::Endnote(_)));\n"
        "        if let (Some(ci), true) = (ci, is_caret) {\n"
        "            slots[ci] = Some(c);\n"
        "        }\n"
        "        c += is_caret as usize;\n"
        "    }\n"
        "    slots\n"
        "}\n"
        "\n"
        "pub(crate) fn caret_control_slots(para: &Paragraph) -> Vec<Option<usize>> {\n",
    ),
    (
        "document_core/helpers.rs",
        "        .filter(|(pos, ctrl)| **pos < utf16_pos && ctrl.is_logical_inline())\n",
        "        // [claude-hwpx sel-note-text-axis] 각주, 미주는 캐럿 칸이 아니다 — 세면 각주 뒤 줄 시작이 한 칸씩 밀린다\n"
        "        .filter(|(pos, ctrl)| {\n"
        "            **pos < utf16_pos\n"
        "                && ctrl.is_logical_inline()\n"
        "                && !matches!(ctrl, Control::Footnote(_) | Control::Endnote(_))\n"
        "        })\n",
    ),
    (
        "document_core/queries/cursor_nav.rs",
        "                {\n"
        "                    let slots = crate::document_core::helpers::caret_control_slots(para);\n"
        "                    if slots.iter().any(|slot| slot.is_some()) {\n",
        "                {\n"
        f"                    // {TAG} 각주, 미주는 캐럿 칸이 아니다(글자 조각 번호, 글 넣기, 문단 길이 모두 글자 축)\n"
        "                    let slots = crate::document_core::helpers::claude_caret_slots_no_notes(para);\n"
        "                    if slots.iter().any(|slot| slot.is_some()) {\n",
    ),
    (
        "document_core/queries/cursor_nav.rs",
        "                                        let ta = crate::document_core::helpers::logical_to_text_offset(para, a).0;\n"
        "                                        let tb = crate::document_core::helpers::logical_to_text_offset(para, b).0;\n",
        "                                        // [claude-hwpx sel-note-text-axis] 글자 축 = 캐럿 위치 - 그 앞 캐럿 칸 개체 수(각주 제외)\n"
        "                                        let claude_slots_before =\n"
        "                                            |pos: usize| slots.iter().filter(|s| s.is_some_and(|s| s < pos)).count();\n"
        "                                        let ta = a - claude_slots_before(a);\n"
        "                                        let tb = b - claude_slots_before(b);\n",
    ),
    (
        "document_core/queries/cursor_nav.rs",
        "                    let slots = crate::document_core::helpers::caret_control_slots(para);\n"
        "                    let mut hit_any = false;\n",
        "                    // [claude-hwpx sel-note-text-axis] 각주, 미주는 캐럿 칸이 아니다\n"
        "                    let slots = crate::document_core::helpers::claude_caret_slots_no_notes(para);\n"
        "                    let mut hit_any = false;\n",
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
