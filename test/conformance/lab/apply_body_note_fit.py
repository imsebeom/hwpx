"""개발용: 본문 문단을 쪽에 담을 때 그 문단 안 각주까지 센다(HWPX 단일 단).

    python apply_body_note_fit.py [--revert]

가이드북 파트2 합본 38쪽(한/글 37쪽): 「프론트엔드(Front-end)⁴²」가 든 9줄 문단을, 앞 각주(36~40)만 뺀 자리에 통째로 넣은 뒤
그 문단의 각주 41, 42 를 등록해 각주 영역(구분선 788px)이 본문 마지막 두 줄(776, 797px) 위로 올라왔다. 한/글은 같은 쪽 구분선이
787.9px 이고 본문은 765px 에서 끊어 나머지 줄을 다음 쪽으로 보낸다(표지가 든 줄은 그 각주까지 들어가야 담는다).

① 문단을 통째로 담을지 볼 때 문단 안 각주 높이를 더한다 ② 줄 단위로 나눌 때 이번 쪽 줄 범위에 든 표지의 각주 높이를 더한다
③ 쪽에 걸친 문단의 각주는 표지가 든 줄이 놓인 쪽에 등록한다(종전 HWPX 는 문단이 끝나는 쪽에 등록했다).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx body-note-fit]"

EDITS = [
    (
        "renderer/typeset.rs",
        "fn composed_footnote_content_height(footnote: &Footnote, dpi: f64) -> f64 {\n",
        f"/// {TAG} 본문 문단 각주의 (표지가 든 줄, 조판한 각주 높이). HWPX 단일 단만\n"
        "fn claude_body_note_lines(st: &TypesetState, para: &Paragraph, dpi: f64) -> Vec<(usize, f64)> {\n"
        "    if !st.profile.hwpx_container() || st.col_count != 1 {\n"
        "        return Vec::new();\n"
        "    }\n"
        "    para.controls\n"
        "        .iter()\n"
        "        .enumerate()\n"
        "        .filter_map(|(ci, c)| match c {\n"
        "            Control::Footnote(f) => Some((\n"
        "                crate::renderer::layout::control_line_seg_index(para, ci).unwrap_or(0),\n"
        "                composed_footnote_content_height(f, dpi),\n"
        "            )),\n"
        "            _ => None,\n"
        "        })\n"
        "        .collect()\n"
        "}\n"
        "\n"
        f"/// {TAG} 줄 from..=to 에 든 표지의 각주를 이 쪽에 더하면 늘어나는 각주 영역 높이(구분선, 각주 사이 포함)\n"
        "fn claude_body_note_extra(st: &TypesetState, notes: &[(usize, f64)], from: usize, to: usize) -> f64 {\n"
        "    let (h, n) = notes\n"
        "        .iter()\n"
        "        .filter(|(l, _)| *l >= from && *l <= to)\n"
        "        .fold((0.0, 0usize), |(h, n), (_, nh)| (h + nh, n + 1));\n"
        "    if n == 0 {\n"
        "        0.0\n"
        "    } else {\n"
        "        (st.projected_footnote_height(h, n) - st.current_footnote_height).max(0.0)\n"
        "    }\n"
        "}\n"
        "\n"
        "fn composed_footnote_content_height(footnote: &Footnote, dpi: f64) -> f64 {\n",
    ),
    (
        "renderer/typeset.rs",
        '        if std::env::var("RHWP_DIAG_6031").is_ok()\n'
        "            && st.current_height + page_end_fit_height > available\n",
        f"        // {TAG} ① 문단을 통째로 담을 때 문단 안 각주까지 들어가야 한다(가이드북 파트2 합본 38쪽, 한/글 37쪽)\n"
        "        let claude_note_lines = claude_body_note_lines(st, para, self.dpi);\n"
        "        let claude_whole_note_h =\n"
        "            claude_body_note_extra(st, &claude_note_lines, 0, fmt.line_heights.len().saturating_sub(1));\n"
        '        if std::env::var("RHWP_DIAG_6031").is_ok()\n'
        "            && st.current_height + page_end_fit_height > available\n",
    ),
    (
        "renderer/typeset.rs",
        "            && (hangul2024_blank_spill\n"
        "                || st.current_height + page_end_fit_height <= available\n",
        "            && (hangul2024_blank_spill\n"
        "                || st.current_height + page_end_fit_height + claude_whole_note_h <= available\n",
    ),
    (
        "renderer/typeset.rs",
        "                let content_h = fmt.line_heights[li];\n"
        "                if cumulative + content_h > avail_for_lines && li > cursor_line {\n",
        "                let content_h = fmt.line_heights[li];\n"
        f"                // {TAG} ② 이번 쪽 줄 범위에 든 표지의 각주까지 들어가야 그 줄을 담는다\n"
        "                let claude_note_h = claude_body_note_extra(st, &claude_note_lines, cursor_line, li);\n"
        "                if cumulative + content_h + claude_note_h > avail_for_lines && li > cursor_line {\n",
    ),
    (
        "renderer/typeset.rs",
        "        if (st.current_height >= available\n"
        "            || remaining < first_line_h\n"
        "            || (stored_whole_para_reset && !hangul2024_split_refit)\n",
        "        if (st.current_height >= available\n"
        f"            // {TAG} 첫 줄에 표지가 있으면 그 각주까지 들어가야 이 쪽에서 시작한다(파트2 합본 101쪽 각주 121)\n"
        "            || remaining < first_line_h + claude_body_note_extra(st, &claude_note_lines, 0, 0)\n"
        "            || (stored_whole_para_reset && !hangul2024_split_refit)\n",
    ),
    (
        "renderer/typeset.rs",
        "                            let routed = if whole_note_owned_by_tail_page {\n"
        "                                None\n"
        "                            } else {\n"
        "                                match collision_routed {\n"
        "                                    Some(route) => route,\n"
        "                                    None => multi_note_routed,\n"
        "                                }\n"
        "                            };\n",
        "                            let routed = if whole_note_owned_by_tail_page {\n"
        "                                None\n"
        "                            } else {\n"
        "                                match collision_routed {\n"
        "                                    Some(route) => route,\n"
        "                                    None => multi_note_routed,\n"
        "                                }\n"
        "                            };\n"
        f"                            // {TAG} ③ 쪽에 걸친 문단의 각주는 표지가 든 줄이 놓인 쪽에 둔다\n"
        "                            let routed = routed.or_else(|| {\n"
        "                                (st.profile.hwpx_container() && st.col_count == 1)\n"
        "                                    .then(|| {\n"
        "                                        crate::renderer::pagination::find_inline_control_target_page(\n"
        "                                            &st.pages,\n"
        "                                            &st.current_items,\n"
        "                                            para_idx,\n"
        "                                            ctrl_idx,\n"
        "                                            para,\n"
        "                                        )\n"
        "                                    })\n"
        "                                    .flatten()\n"
        "                            });\n",
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
