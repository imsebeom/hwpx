"""개발용: tac-row-ladder 의 칸 사다리 끝에 칸 안 위아래 배치(문단 기준) 그림, 도형, 표의 바닥도 넣는다.

    python apply_ladder_pic_bottom.py [--revert]

근거:
  - 결과보고서 21:27 판 42쪽 216번 표 「관련 사진」 칸: 그림(5308, 5983, 6855, treatAsChar=0, TopAndBottom)이 저장 줄(높이 200)에 잡히지 않아
    행이 선언 67.7, 32.8px 에 머물고 그림은 행 밖으로 겹쳤다. 한/글은 그림 높이로 행을 그린다.
  - 정답본 d347 76번 표: 칸 안 표(treatAsChar=0, 13144)도 저장 줄에 안 잡혀 사다리가 16778 로 행을 줄였다(한/글 29822). 글자처럼 취급 칸 안
    표는 저장 줄이 담으므로 넣지 않는다(결과보고서 49번 표).
큰 값을 고르므로 저장 줄이 개체 자리를 이미 담은 칸은 그대로다. ladder-stack-frag 보다 먼저 적용한다(그 패치가 이 블록의 쌓기 줄을 바꾼다).
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx ladder-pic-bottom]"

EDITS = [
    (
        "renderer/height_measurer.rs",
        (
            "                        next_top = top.saturating_add(s.line_height).saturating_add(s.line_spacing.max(0));\n"
            "                    }\n"
            "                    end\n"
            "                };\n"
            "                let pad = if c.apply_inner_margin { &c.padding } else { &table.padding };\n"
        ),
        (
            "                        next_top = top.saturating_add(s.line_height).saturating_add(s.line_spacing.max(0));\n"
            "                    }\n"
            f"                    // {TAG} 칸 안 위아래 배치(문단 기준) 그림, 도형, 표는 저장 줄에 안 잡힌다 — 그 바닥도 사다리 끝으로 본다\n"
            "                    // (결과보고서 216번 표 사진 칸: 줄 200, 그림 5308 → 한/글은 그림 높이로 행을 그린다)\n"
            "                    for p in &c.paragraphs {\n"
            "                        let para_top = p.line_segs.first().map(|s| s.vertical_pos).unwrap_or(0);\n"
            "                        for ctl in &p.controls {\n"
            "                            let common = match ctl {\n"
            "                                Control::Picture(pic) => &pic.common,\n"
            "                                Control::Shape(sh) => sh.common(),\n"
            "                                // 위아래 배치 칸 안 표도 저장 줄에 안 잡힌다(정답본 d347 76번 표: 사다리 16778, 한/글 29822)\n"
            "                                Control::Table(t) => &t.common,\n"
            "                                _ => continue,\n"
            "                            };\n"
            "                            if common.treat_as_char\n"
            "                                || !matches!(common.text_wrap, TextWrap::TopAndBottom)\n"
            "                                || !matches!(common.vert_rel_to, VertRelTo::Para)\n"
            "                            {\n"
            "                                continue;\n"
            "                            }\n"
            "                            let bottom = para_top\n"
            "                                .saturating_add((common.vertical_offset as i32).max(0))\n"
            "                                .saturating_add(common.height.min(i32::MAX as u32) as i32)\n"
            "                                .saturating_add(common.margin.top as i32)\n"
            "                                .saturating_add(common.margin.bottom as i32);\n"
            "                            end = end.max(bottom);\n"
            "                        }\n"
            "                    }\n"
            "                    end\n"
            "                };\n"
            "                let pad = if c.apply_inner_margin { &c.padding } else { &table.padding };\n"
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
