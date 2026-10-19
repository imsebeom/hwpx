"""개발용: HWPX 에서 글 없는 문단에 자리 차지 표(문단 기준)가 둘 이상이면, 호스트 줄(줄 높이 + 줄 간격)을 그 쪽에 놓인 마지막 표 아래에 둔다.

    python apply_multi_float_host_line.py [--revert]

사본 실험(exp/make_multitbl.py, d019 p6 표 4800): 표 하나면 호스트 줄은 표 위(폭 0)라 다음 문단 = 호스트 윗변 + 4800.
표 둘이면 둘째 표가 첫 표 아래에 쌓이고 호스트 줄은 두 표 아래(윗변 + 9600), 다음 문단은 그 아래 1600. 표 셋이면 세 표 아래(+14400).
둘째 표 오프셋 2000 도 같다. 표 하나 + 탭(줄에 내용)이면 줄이 표 아래로 가는데, 엔진은 이것을 이미 맞게 둔다.
d322 p77(둘째 표가 다음 쪽으로 미뤄짐)은 호스트 줄이 첫 표 아래(52853)에 있고 p78 이 그 아래 1600 이다 — 줄은 문단이 시작한 쪽에 남는다.
엔진은 표 둘 이상인 빈 문단에서 호스트 줄을 세지 않아 뒤 글이 21.3px 위로 올라왔다(t_many 32쪽 12줄, 한/글 11줄).
- 조판: 마지막 표의 뒤 간격에 호스트 줄을 더한다. 마지막 표를 미루면 그 자리에서 더하고, 미룬 표를 꺼낼 때는 뺀다.
- 그리기: 문단의 첫 표가 이 쪽에 있고 같은 문단의 뒤 표가 이 쪽에 더 없으면 그 표 뒤 y 에 호스트 줄을 더한다.
줄 배치가 저장된 문단(한/글 원본)은 다음 문단 vpos 가 이미 담으니 건드리지 않는다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx multi-float-host-line]"

EDITS = [
    (
        "renderer/mod.rs",
        "pub(crate) fn para_has_no_stored_line_segs(p: &crate::model::paragraph::Paragraph) -> bool {\n"
        "    p.line_segs.is_empty() || p.line_segs.iter().all(|s| s.tag & 0x8000_0000 != 0)\n"
        "}\n",
        "pub(crate) fn para_has_no_stored_line_segs(p: &crate::model::paragraph::Paragraph) -> bool {\n"
        "    p.line_segs.is_empty() || p.line_segs.iter().all(|s| s.tag & 0x8000_0000 != 0)\n"
        "}\n"
        "\n"
        f"/// {TAG} 줄 배치 없는 글 없는 문단에 자리 차지 표(문단 기준)만 둘 이상이면 (첫 표, 마지막 표, 호스트 줄 높이 + 줄 간격 HU).\n"
        "/// 한/글은 이 호스트 줄을 그 쪽에 놓인 마지막 표 아래에 둔다(표 하나면 표 위, 폭 0 이라 높이를 쓰지 않는다).\n"
        "pub(crate) fn claude_multi_float_host_line(\n"
        "    p: &crate::model::paragraph::Paragraph,\n"
        ") -> Option<(usize, usize, i32)> {\n"
        "    if !p.text.is_empty() || !para_has_no_stored_line_segs(p) {\n"
        "        return None;\n"
        "    }\n"
        "    let mut floats = Vec::new();\n"
        "    for (i, c) in p.controls.iter().enumerate() {\n"
        "        match c {\n"
        "            crate::model::control::Control::Table(t)\n"
        "                if !t.common.treat_as_char\n"
        "                    && matches!(t.common.text_wrap, crate::model::shape::TextWrap::TopAndBottom)\n"
        "                    && matches!(t.common.vert_rel_to, crate::model::shape::VertRelTo::Para) =>\n"
        "            {\n"
        "                floats.push(i)\n"
        "            }\n"
        "            crate::model::control::Control::Table(_)\n"
        "            | crate::model::control::Control::Picture(_)\n"
        "            | crate::model::control::Control::Shape(_) => return None,\n"
        "            _ => {}\n"
        "        }\n"
        "    }\n"
        "    if floats.len() < 2 {\n"
        "        return None;\n"
        "    }\n"
        "    let seg = p.line_segs.first()?;\n"
        "    let hu = seg.line_height + seg.line_spacing.max(0);\n"
        "    (hu > 0).then(|| (floats[0], floats[floats.len() - 1], hu))\n"
        "}\n",
    ),
    (
        "renderer/typeset.rs",
        "            + stored_empty_anchor_host_line_tail;\n        let host_spacing = HostSpacing {\n",
        "            + stored_empty_anchor_host_line_tail;\n"
        f"        // {TAG} 표 둘 이상인 빈 문단의 호스트 줄은 마지막 표 아래에 놓인다\n"
        "        let after = after\n"
        "            + self.claude_multi_float_host_line_px(para, ctrl_idx);\n"
        "        let host_spacing = HostSpacing {\n",
    ),
    (
        "renderer/typeset.rs",
        "    fn flush_deferred_table_controls(\n",
        f"    /// {TAG} HWPX 의 표 둘 이상인 빈 문단에서 이 표가 마지막 표면 호스트 줄 높이(px), 아니면 0\n"
        "    fn claude_multi_float_host_line_px(&self, para: &Paragraph, ctrl_idx: usize) -> f64 {\n"
        "        if !self.profile.get().hwpx_container() {\n"
        "            return 0.0;\n"
        "        }\n"
        "        match crate::renderer::claude_multi_float_host_line(para) {\n"
        "            Some((_, last, hu)) if last == ctrl_idx => hwpunit_to_px(hu, self.dpi),\n"
        "            _ => 0.0,\n"
        "        }\n"
        "    }\n"
        "\n"
        "    fn flush_deferred_table_controls(\n",
    ),
    (
        "renderer/typeset.rs",
        "            let mt = measured_tables.iter().find(|mt| {\n"
        "                mt.para_index == deferred.para_index && mt.control_index == deferred.control_index\n"
        "            });\n",
        f"            // {TAG} 미룬 마지막 표의 호스트 줄은 문단이 시작한 쪽에서 이미 셌다\n"
        "            let mut ft = ft;\n"
        "            let claude_host_line = self.claude_multi_float_host_line_px(para, deferred.control_index);\n"
        "            ft.host_spacing.after -= claude_host_line;\n"
        "            ft.host_spacing.after_for_fit -= claude_host_line;\n"
        "            let mt = measured_tables.iter().find(|mt| {\n"
        "                mt.para_index == deferred.para_index && mt.control_index == deferred.control_index\n"
        "            });\n",
    ),
    (
        "renderer/typeset.rs",
        "                                para_start_height,\n"
        "                            });\n"
        "                            continue;\n"
        "                        }\n"
        "                        let pages_before_block_table = st.pages.len();\n",
        "                                para_start_height,\n"
        "                            });\n"
        f"                            // {TAG} 마지막 표를 미루면 호스트 줄은 이 쪽(첫 표 아래)에 남는다(d322 p77)\n"
        "                            st.current_height += self.claude_multi_float_host_line_px(para, ctrl_idx);\n"
        "                            continue;\n"
        "                        }\n"
        "                        let pages_before_block_table = st.pages.len();\n",
    ),
    (
        "renderer/layout.rs",
        "                y_offset = global_y_before.max(lane_flow_bottom);\n            }\n            if tac_seg_applied {\n",
        "                y_offset = global_y_before.max(lane_flow_bottom);\n"
        f"                // {TAG} 표 둘 이상인 빈 문단: 첫 표가 이 쪽에 있고 뒤 표가 이 쪽에 더 없으면 호스트 줄을 이 표 아래에 둔다\n"
        "                if self.profile.get().hwpx_container() {\n"
        "                    if let Some((first, last, hu)) = crate::renderer::claude_multi_float_host_line(para) {\n"
        "                        if control_index >= first && control_index <= last {\n"
        "                            // 흐름은 쌓인 표 바닥 + 이 표 바깥 아래 여백(첫 표 오프셋과 표마다 여백 위아래가 다 들어간다)\n"
        "                            if let Some(Control::Table(t)) = para.controls.get(control_index) {\n"
        "                                y_offset = lanes.max_bottom()\n"
        "                                    + hwpunit_to_px(t.outer_margin_bottom as i32, self.dpi);\n"
        "                            }\n"
        "                            let on_page = |ci: usize| {\n"
        "                                page_content.column_contents.iter().any(|cc| {\n"
        "                                    cc.items.iter().any(|it| {\n"
        "                                        matches!(it, PageItem::Table { para_index: pi, control_index: c }\n"
        "                                            if *pi == para_index && *c == ci)\n"
        "                                    })\n"
        "                                })\n"
        "                            };\n"
        "                            if on_page(first) && !(control_index + 1..=last).any(|ci| on_page(ci)) {\n"
        "                                y_offset += hwpunit_to_px(hu, self.dpi);\n"
        "                            }\n"
        "                        }\n"
        "                    }\n"
        "                }\n"
        "            }\n"
        "            if tac_seg_applied {\n",
    ),
    (
        "renderer/layout.rs",
        "                    let lane_top = para_float_lanes\n"
        "                        .entry(para_index)\n"
        "                        .or_default()\n"
        "                        .pushed_top(x_start, x_end, raw_top);\n"
        "                    para_float_lane_info = Some((x_start, x_end, raw_top, lane_top, y_offset));\n",
        "                    let mut lane_top = para_float_lanes\n"
        "                        .entry(para_index)\n"
        "                        .or_default()\n"
        "                        .pushed_top(x_start, x_end, raw_top);\n"
        f"                    // {TAG} 표 둘 이상인 빈 문단의 뒤 표는 오프셋을 쓰지 않고 앞 표 아래에 쌓인다:\n"
        "                    // 앞 표 바닥 + 앞 표 바깥 아래 여백 + 이 표 바깥 위 여백(사본 실험 two_om, two_om_off0, two_off375)\n"
        "                    if self.profile.get().hwpx_container() {\n"
        "                        if let Some((first, _, _)) = crate::renderer::claude_multi_float_host_line(para) {\n"
        "                            let lanes_bottom = para_float_lanes\n"
        "                                .get(&para_index)\n"
        "                                .map(|l| l.max_bottom())\n"
        "                                .unwrap_or(0.0);\n"
        "                            let prev_om_bottom = para.controls[..control_index.min(para.controls.len())]\n"
        "                                .iter()\n"
        "                                .rev()\n"
        "                                .find_map(|c| match c {\n"
        "                                    Control::Table(pt) => Some(pt.outer_margin_bottom as i32),\n"
        "                                    _ => None,\n"
        "                                });\n"
        "                            if control_index > first && lanes_bottom > 0.0 {\n"
        "                                if let Some(prev_om_bottom) = prev_om_bottom {\n"
        "                                    lane_top = lanes_bottom\n"
        "                                        + hwpunit_to_px(prev_om_bottom, self.dpi)\n"
        "                                        + hwpunit_to_px(t.outer_margin_top as i32, self.dpi);\n"
        "                                }\n"
        "                            }\n"
        "                        }\n"
        "                    }\n"
        "                    para_float_lane_info = Some((x_start, x_end, raw_top, lane_top, y_offset));\n",
    ),
    (
        "renderer/layout.rs",
        "                lanes.place(x_start, x_end, raw_top, reserved_height);\n",
        f"                // {TAG} 쌓은 뒤 표는 고친 위치(lane_top)로 기록해야 바닥이 맞는다\n"
        "                let claude_place_top = if self.profile.get().hwpx_container()\n"
        "                    && crate::renderer::claude_multi_float_host_line(para).is_some()\n"
        "                {\n"
        "                    lane_top\n"
        "                } else {\n"
        "                    raw_top\n"
        "                };\n"
        "                lanes.place(x_start, x_end, claude_place_top, reserved_height);\n",
    ),
    (
        "renderer/typeset.rs",
        "        let lane_top = lanes.pushed_top(x_start, x_end, raw_top);\n"
        "        let lane_bottom = lane_top + reserved_height;\n"
        "\n"
        "        if lane_bottom > available + 0.5 {\n"
        "            return false;\n"
        "        }\n"
        "\n"
        "        st.current_items.push(PageItem::Table {\n"
        "            para_index: para_idx,\n"
        "            control_index: ctrl_idx,\n"
        "        });\n"
        "        lanes.place(x_start, x_end, raw_top, reserved_height);\n",
        "        let mut lane_top = lanes.pushed_top(x_start, x_end, raw_top);\n"
        f"        // {TAG} 표 둘 이상인 빈 문단: 첫 표는 문단 위치 + 오프셋 + 바깥 위 여백, 뒤 표는 앞 표 아래(오프셋 없이)\n"
        "        // + 바깥 위 여백. 예약은 표 높이 + 뒤 간격 전체(바깥 아래 여백, 마지막 표면 호스트 줄)\n"
        "        let claude_multi = is_topbottom_para_float\n"
        "            && st.profile.hwpx_container()\n"
        "            && crate::renderer::claude_multi_float_host_line(para).is_some();\n"
        "        let mut reserved_height = reserved_height;\n"
        "        if claude_multi {\n"
        "            let claude_om_top = hwpunit_to_px(table.outer_margin_top as i32, self.dpi);\n"
        "            lane_top = if lanes.max_bottom() > 0.0 {\n"
        "                lanes.max_bottom() + claude_om_top\n"
        "            } else {\n"
        "                raw_top + claude_om_top\n"
        "            };\n"
        "            reserved_height = ft.effective_height + ft.host_spacing.after;\n"
        "        }\n"
        "        let lane_bottom = lane_top + reserved_height;\n"
        "\n"
        "        if lane_bottom > available + 0.5 {\n"
        "            return false;\n"
        "        }\n"
        "\n"
        "        st.current_items.push(PageItem::Table {\n"
        "            para_index: para_idx,\n"
        "            control_index: ctrl_idx,\n"
        "        });\n"
        "        lanes.place(\n"
        "            x_start,\n"
        "            x_end,\n"
        "            if claude_multi { lane_top } else { raw_top },\n"
        "            reserved_height,\n"
        "        );\n",
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
