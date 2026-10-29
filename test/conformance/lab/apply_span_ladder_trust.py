"""개발용: HWPX 글자처럼 취급 표의 여러 행에 걸친 칸도, 저장 줄이 그림 아래로 밀려 있으면 그림을 따로 더하지 않고 저장 줄 끝으로 잰다.

    python apply_span_ladder_trust.py [--revert]

근거(2026-10-29 결과보고서 21:11 판 160번 표 10행 c0, 두 행에 걸친 칸): 위아래 배치 그림(1484, 세로 오프셋 -621) 뒤 첫 줄이 1484 에서
시작하고 저장 줄 끝은 3234 + 850 = 4084 다. 한/글은 10~11행을 4084 + 칸 여백 282 = 58.3px 로 그린다. 엔진은 걸친 칸을
「글 높이 + 그림 높이」로만 재 65.7px(7.4px 큼)였다. 한 행 칸은 같은 증거(뒤 줄이 그림 아래에서 시작)로 저장 줄을 믿는다(#6208 계열
ladder_pushed_following_line). 줄은 차례로 쌓아 잰다(cell-floor-stack 과 같은 셈).
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx span-ladder-trust]"

EDITS = [
    (
        "renderer/height_measurer.rs",
        "                let combined: f64 = (r..r + span).map(|i| row_heights[i]).sum();\n",
        (
            f"                // {TAG} HWPX 글자처럼 취급 표의 걸친 칸: 뒤 줄이 그림 아래에서 시작하면 저장 줄이 그림 자리를 담았다 — 그림을 또 더하지 않는다\n"
            "                // (결과보고서 160번 표 10행: 한/글 58.3px = 줄 끝 4084 + 여백, 엔진 65.7px)\n"
            "                let required_height = if !self.is_native_hwp5\n"
            "                    && !self.is_hwp3_variant\n"
            "                    && table.common.treat_as_char\n"
            "                    && non_inline_h > 0.0\n"
            "                    && cell.text_direction == 0\n"
            "                    && cell.paragraphs.iter().all(|p| {\n"
            "                        !p.line_segs.is_empty() && p.line_segs.iter().all(|s| s.tag & 0x8000_0000 == 0)\n"
            "                    })\n"
            "                    && cell.paragraphs.iter().enumerate().any(|(i, pp)| {\n"
            "                        let obj_h = pp\n"
            "                            .controls\n"
            "                            .iter()\n"
            "                            .filter_map(|c| match c {\n"
            "                                Control::Picture(pic) if !pic.common.treat_as_char => {\n"
            "                                    Some(self.non_inline_control_flow_height(&pic.common))\n"
            "                                }\n"
            "                                Control::Shape(sh) if !sh.common().treat_as_char => {\n"
            "                                    Some(self.non_inline_control_flow_height(sh.common()))\n"
            "                                }\n"
            "                                _ => None,\n"
            "                            })\n"
            "                            .fold(0.0f64, f64::max);\n"
            "                        let own_top = pp\n"
            "                            .line_segs\n"
            "                            .first()\n"
            "                            .map(|s| hwpunit_to_px(s.vertical_pos, self.dpi))\n"
            "                            .unwrap_or(0.0);\n"
            "                        obj_h > 0.0\n"
            "                            && cell.paragraphs[i + 1..]\n"
            "                                .iter()\n"
            "                                .find_map(|later| later.line_segs.first())\n"
            "                                .is_some_and(|s| hwpunit_to_px(s.vertical_pos, self.dpi) + 0.5 >= own_top + obj_h)\n"
            "                    }) {\n"
            "                    let (mut next_top, mut end) = (0i64, 0i64);\n"
            "                    for s in cell.paragraphs.iter().flat_map(|p| p.line_segs.iter()) {\n"
            "                        let top = i64::from(s.vertical_pos).max(next_top);\n"
            "                        end = end.max(top + i64::from(s.line_height));\n"
            "                        next_top = top + i64::from(s.line_height) + i64::from(s.line_spacing.max(0));\n"
            "                    }\n"
            "                    hwpunit_to_px(end as i32, self.dpi).max(nested_bottom).max(wrap_bottom) + pad_top + pad_bottom\n"
            "                } else {\n"
            "                    required_height\n"
            "                };\n"
            "                let combined: f64 = (r..r + span).map(|i| row_heights[i]).sum();\n"
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
