"""개발용: 엔진이 만든 줄(줄 배치 없는 HWPX, 편집 뒤 다시 만든 줄)의 글자처럼 취급 표 문단은 전진을 cap 으로 깎지 않는다.

    python apply_tac_cap_synth.py [--revert]

근거(2026-10-18 정답본 한/글 줄 기록, harvest_tacstep.py): 글 없이 글자처럼 취급 표 하나만 든 본문 문단 1,700건 가운데
1,685건이 다음 문단까지 「줄 높이 + 줄 간격 전체(+ 문단 아래, 다음 문단 위 간격)」만큼 내려간다. 엔진 cap
「줄 높이 + 줄 간격 절반 + 바깥 위 여백」과 맞는 것은 0건이다. 저장 줄이 있으면 tac-cap-ladder 가 저장 스텝으로 cap 을 풀지만,
엔진이 만든 줄에는 그 증거가 없어 표마다 1~2px 덜 내려갔다(d193 1쪽: 표 셋에 −6.7px, 한/글보다 한 줄 더 담아 쪽이 갈림).
cap 만 풀면 쪽수 95.1 → 95.4% 인데 문단 쪽 98.7 → 94.7% 였다. 그동안 cap 이 덮던 결함이 드러났기 때문이다. 한 줄짜리
글자처럼 취급 표의 쪽 끝 들어감 판정(블록 표 경로 whole_fit)이 뒤 줄 간격까지 요구해, d292 p75(표 379.9px)가 남은 386.7px 에
못 들어갔다. 한/글은 「위 간격 + 줄 높이」만 요구한다(tac-caption-line 과 같은 마지막 줄 규칙). 둘을 함께 넣으면
쪽수 95.7%, 문단 쪽 99.2%, 줄바꿈 불일치 그대로. 새로 어긋난 d010 은 p8 줄바꿈 불일치(한/글 1줄, rhwp 2줄)를 cap 이 덮던 것이고,
d034 p400(그룹 개체 줄)은 일반 문단 경로의 쪽 끝 판정이 앞 항목이 표일 때만 뒤 간격을 빼서였다. 글 없이 글자처럼 취급 개체만 든
문단도 빼도록 넣었다(글 문단까지 넓히면 d033 이 틀린다). 셋을 함께 넣어 쪽수 96.0%, 문단 쪽 99.2%.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx tac-cap-synth]"

EDITS = [
    (
        "renderer/typeset.rs",
        "            let cap = if ladder_omits_spacing || ladder_matches_total {\n"
        "                fmt.total_height\n"
        "            } else {\n"
        "                cap\n"
        "            };\n",
        f"            // {TAG} 엔진이 만든 줄의 HWPX 문단은 줄 높이 + 줄 간격 전체로 전진한다(harvest_tacstep.py: 한/글 1,685건 모두 전체,\n"
        "            // cap 과 맞는 것 0건). 저장 사다리 증거(위 두 판정)가 없어 cap 이 표마다 줄 간격 절반을 깎았다(d193)\n"
        "            // 줄 하나뿐인(표만 든) 문단만 — 글 줄이 앞에 있으면 표가 다음 쪽으로 갈 때 fmt.total 이 앞 쪽 글 줄까지 품는다(d043 p6)\n"
        "            // 빈칸만 있는 문단도 글 없는 문단이다(d268 둘째 구역 p152 「 」 + 표: 한/글 새 조판 4488 + 1200, cap 이 320 깎았다)\n"
        "            let claude_synth_hwpx = st.profile.hwpx_container()\n"
        "                && para.line_segs.len() == 1\n"
        "                && !para_has_non_whitespace_text(para)\n"
        "                && para.line_segs.first().is_some_and(|s| {\n"
        "                    s.tag & crate::model::paragraph::LineSeg::TAG_IMPLEMENTATION_PROPERTY != 0\n"
        "                });\n"
        "            let cap = if ladder_omits_spacing || ladder_matches_total || claude_synth_hwpx {\n"
        "                fmt.total_height\n"
        "            } else {\n"
        "                cap\n"
        "            };\n",
    ),
    (
        "renderer/typeset.rs",
        "        if table.common.treat_as_char\n"
        "            && fmt.line_heights.len() == 1\n"
        "            && fmt.total_height > table_total\n"
        "        {\n"
        "            table_total = fmt.total_height;\n"
        "        }\n",
        "        if table.common.treat_as_char\n"
        "            && fmt.line_heights.len() == 1\n"
        "            && fmt.total_height > table_total\n"
        "        {\n"
        "            table_total = fmt.total_height;\n"
        "        }\n"
        f"        // {TAG} 한 줄짜리 글자처럼 취급 표가 쪽 끝에 들어가려면 한/글은 「위 간격 + 줄 높이」(표 + 바깥 여백)만 요구한다\n"
        "        // (tac-caption-line 과 같은 마지막 줄 규칙). table_total 은 뒤 줄 간격(host_spacing.after_for_fit, 위 정합의 fmt.total)을\n"
        "        // 품어, d292 p75(표 379.9px)가 남은 386.7px 에 못 들어가고 다음 쪽으로 갔다. 판정에서만 그 꼬리를 뺀다\n"
        "        let claude_fit_tail = if table.common.treat_as_char && fmt.line_heights.len() == 1 {\n"
        "            let need = (fmt.spacing_before + fmt.line_heights[0])\n"
        "                .max(ft.effective_height + ft.host_spacing.before);\n"
        "            (table_total - need).max(0.0)\n"
        "        } else {\n"
        "            0.0\n"
        "        };\n",
    ),
    (
        "renderer/typeset.rs",
        "        let whole_fit_table_total = if uses_painted_row_footprint_for_whole_fit {\n"
        "            table_total.max(measured_row_table_height.unwrap_or(0.0) + host_spacing_total)\n"
        "        } else {\n"
        "            table_total\n"
        "        };\n",
        "        let whole_fit_table_total = if uses_painted_row_footprint_for_whole_fit {\n"
        "            table_total.max(measured_row_table_height.unwrap_or(0.0) + host_spacing_total)\n"
        "        } else {\n"
        f"            // {TAG} 한 줄짜리 글자처럼 취급 표의 뒤 간격은 들어감 판정에서 뺀다(위 claude_fit_tail)\n"
        "            table_total - claude_fit_tail\n"
        "        };\n",
    ),
    (
        "renderer/typeset.rs",
        "                let overflow_threshold = if prev_is_table {\n",
        f"                // {TAG} 글 없이 글자처럼 취급 개체만 든 문단도 마지막 줄 뒤 줄 간격 없이 들어가면 된다(표 경로와 같은 마지막 줄 규칙).\n"
        "                // 앞 표들이 한/글만큼 내려가자 d034 p400(그룹 개체 줄 17383, 남은 자리에 들어감)이 뒤 간격 때문에 다음 쪽으로 밀렸다.\n"
        "                // 글 문단까지 넓히면 d033 이 틀려 개체만 든 문단으로 좁힌다\n"
        "                let claude_object_only = st.profile.hwpx_container()\n"
        "                    && !para_has_visible_text(para)\n"
        "                    && para.controls.iter().any(|c| match c {\n"
        "                        Control::Picture(p) => p.common.treat_as_char,\n"
        "                        Control::Shape(s) => s.common().treat_as_char,\n"
        "                        _ => false,\n"
        "                    });\n"
        "                let overflow_threshold = if prev_is_table || claude_object_only {\n",
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
