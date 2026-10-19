"""개발용: 본문 캐럿 그리기에서 각주, 미주 표지 자리를 에디터 캐럿 축(각주를 세지 않음)으로 잡는다.

    python apply_note_caret_axis.py [--revert]

근거(2026-10-19, 가이드북 3장 _261019_19 p33 각주 11, 「(Hosting)」 183~191 뒤, 「, 」 192~):
캐럿 192 에 글을 넣으면 각주 앞(각주가 글자 193 으로 밀림), 193 에 넣으면 「,」 뒤에 들어간다(글자 축, 각주는 칸이 아님).
그런데 캐럿 그리기는 표지 자리를 논리 축(각주를 칸으로 셈)으로 잡고 「표지 자리 + 1 = 표지 바로 뒤」로 그려,
193 을 「,」 앞(413.5)에 그렸다(글은 416.4 뒤에 들어감). 한 문단 둘째 각주부터는 논리 축이 앞선 각주 수만큼 밀려 그 자리도 어긋났다.
칸 안 캐럿은 이 특례가 없어 이미 맞다(시험 칸 「등록」 뒤 각주: 12 → 「,」 뒤).
표지 자리 = 그 각주 앞 글자 수 + 그 앞 캐럿 칸 개체 수(글자처럼 취급 표, 그림, 수식. 각주 제외). 표지 앞 캐럿만 표지 왼쪽에 그린다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx note-caret-axis]"

EDITS = [
    (
        "document_core/helpers.rs",
        "pub(crate) fn caret_control_slots(para: &Paragraph) -> Vec<Option<usize>> {\n",
        f"/// {TAG} 각주, 미주 표지의 캐럿 자리(각주를 세지 않는 에디터 캐럿 축). 컨트롤 번호로 찾는다.\n"
        "pub(crate) fn claude_note_caret_positions(para: &Paragraph) -> Vec<(usize, usize)> {\n"
        "    let mut out = Vec::new();\n"
        "    let mut c = 0usize;\n"
        "    for (ci, is_caret, _) in caret_axis_items(para) {\n"
        "        let is_note = ci.is_some_and(|ci| matches!(para.controls[ci], Control::Footnote(_) | Control::Endnote(_)));\n"
        "        if let (Some(ci), true) = (ci, is_note) {\n"
        "            out.push((ci, c));\n"
        "        }\n"
        "        c += (is_caret && !is_note) as usize;\n"
        "    }\n"
        "    out\n"
        "}\n"
        "\n"
        "pub(crate) fn caret_control_slots(para: &Paragraph) -> Vec<Option<usize>> {\n",
    ),
    (
        "document_core/queries/cursor_rect.rs",
        "        let footnote_marker_positions: Vec<(usize, usize)> = self\n"
        "            .get_render_paragraph_ref(section_idx, para_idx)\n"
        "            .ok()\n"
        "            .map(|para| {\n"
        "                let ctrl_positions = find_logical_control_positions(para);\n"
        "                para.controls\n"
        "                    .iter()\n"
        "                    .enumerate()\n"
        "                    .filter(|(_, ctrl)| matches!(ctrl, Control::Footnote(_) | Control::Endnote(_)))\n"
        "                    .filter_map(|(ci, _)| ctrl_positions.get(ci).copied().map(|pos| (ci, pos)))\n"
        "                    .collect()\n"
        "            })\n"
        "            .unwrap_or_default();\n",
        f"        // {TAG} 표지 자리는 각주를 세지 않는 캐럿 축(글 넣기와 같은 축)\n"
        "        let footnote_marker_positions: Vec<(usize, usize)> = self\n"
        "            .get_render_paragraph_ref(section_idx, para_idx)\n"
        "            .ok()\n"
        "            .map(crate::document_core::helpers::claude_note_caret_positions)\n"
        "            .unwrap_or_default();\n",
    ),
    (
        "document_core/queries/cursor_rect.rs",
        "                        if offset == *marker_pos || offset == *marker_pos + 1 {\n"
        "                            return Some(CursorHit {\n"
        "                                page_index,\n"
        "                                x: if offset == *marker_pos {\n"
        "                                    node.bbox.x\n"
        "                                } else {\n"
        "                                    node.bbox.x + node.bbox.width\n"
        "                                },\n",
        "                        // [claude-hwpx note-caret-axis] 표지 자리 캐럿은 표지 앞(그 자리에 넣은 글은 각주 앞에 들어간다). 다음 자리는 글자 조각이 그린다\n"
        "                        if offset == *marker_pos {\n"
        "                            return Some(CursorHit {\n"
        "                                page_index,\n"
        "                                x: node.bbox.x,\n",
    ),
    (
        "document_core/queries/cursor_nav.rs",
        "         -> Option<CursorHit> {\n"
        "            if let Some(target) = cell_target {\n"
        "                find_cell_cursor(&tree.root, target, para_idx, offset, page, bias)\n"
        "            } else {\n"
        "                find_body_cursor(\n"
        "                    &tree.root,\n"
        "                    section_idx,\n"
        "                    para_idx,\n"
        "                    self.get_render_paragraph_ref(section_idx, para_idx).ok(),\n"
        "                    offset,\n"
        "                    page,\n"
        "                    bias,\n"
        "                )\n"
        "            }\n"
        "        };\n",
        "         -> Option<CursorHit> {\n"
        "            let claude_find = |bias: CursorBias| {\n"
        "            if let Some(target) = cell_target {\n"
        "                find_cell_cursor(&tree.root, target, para_idx, offset, page, bias)\n"
        "            } else {\n"
        "                find_body_cursor(\n"
        "                    &tree.root,\n"
        "                    section_idx,\n"
        "                    para_idx,\n"
        "                    self.get_render_paragraph_ref(section_idx, para_idx).ok(),\n"
        "                    offset,\n"
        "                    page,\n"
        "                    bias,\n"
        "                )\n"
        "            }\n"
        "            };\n"
        "            // [claude-hwpx note-caret-axis] 선택 시작이 각주 표지 자리(표지 앞 캐럿)면 표지부터 칠한다 — 앞 글자 조각이 같은 줄에서\n"
        "            // 표지 폭(글자 크기 1.5배 안)만큼 왼쪽에서 끝나면 그 끝을 쓴다. 칸 안 표지 노드는 칸 정보가 없어 조각 끝으로 찾는다\n"
        "            let hit = claude_find(bias)?;\n"
        "            if matches!(bias, CursorBias::Leading) {\n"
        "                if let Some(t) = claude_find(CursorBias::Trailing) {\n"
        "                    if t.page == hit.page\n"
        "                        && (t.y - hit.y).abs() < 1.0\n"
        "                        && t.x < hit.x - 0.5\n"
        "                        && hit.x - t.x < hit.h * 1.5\n"
        "                    {\n"
        "                        return Some(CursorHit { x: t.x, ..hit });\n"
        "                    }\n"
        "                }\n"
        "            }\n"
        "            Some(hit)\n"
        "        };\n",
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
