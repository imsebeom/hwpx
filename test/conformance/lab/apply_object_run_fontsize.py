"""개발용: 글 없이 글자처럼 취급 개체만 있는 줄의 줄 간격 기준 글자 크기를 「그 줄 개체 자리의 글자 모양 중 가장 큰 것」으로 잡는다.

    python apply_object_run_fontsize.py [--revert]

근거(d126 p0): 구역 정의가 든 11pt run 뒤 18pt run 에 글자처럼 취급 표가 든 문단에서 한/글은 줄 간격을 18pt 기준
(160% → 1080)으로 잡는다. 엔진(control-line-charpr)은 줄 시작 자리(구역 정의, 11pt)의 글자 모양을 써서 660 을 잡았고
다음 문단이 420 HU 위로 왔다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx object-run-fontsize]"
REL = "renderer/composer/line_breaking.rs"

EDITS = [
    (
        REL,
        "            let mut line_specs: Vec<(u32, i32, i32)> = Vec::new();\n"
        "            let mut line_start = 0u32;\n"
        "            let mut line_width = 0i32;\n"
        "            let mut line_height = 0i32;\n"
        "\n"
        "            for (utf16_start, (ctrl_width, ctrl_height)) in inline_sizes.iter().copied() {\n"
        "                if line_width > 0 && line_width + ctrl_width > max_line_width {\n"
        "                    line_specs.push((line_start, line_width, line_height));\n"
        "                    line_start = utf16_start;\n"
        "                    line_width = 0;\n"
        "                    line_height = 0;\n"
        "                }\n"
        "                line_width += ctrl_width;\n"
        "                line_height = line_height.max(ctrl_height);\n"
        "            }\n"
        "            line_specs.push((line_start, line_width, line_height));\n",
        f"            // {TAG} 줄마다 그 줄에 든 개체 자리의 글자 크기 중 가장 큰 것도 들고 다닌다(줄 간격 기준, d126 p0)\n"
        "            let font_size_at = |pos: u32| -> f64 {\n"
        "                para.char_shapes\n"
        "                    .iter()\n"
        "                    .rev()\n"
        "                    .find(|c| c.start_pos <= pos)\n"
        "                    .or_else(|| para.char_shapes.first())\n"
        "                    .and_then(|c| styles.char_styles.get(c.char_shape_id as usize))\n"
        "                    .map(|style| style.font_size)\n"
        "                    .unwrap_or(0.0)\n"
        "            };\n"
        "            let mut line_specs: Vec<(u32, i32, i32, f64)> = Vec::new();\n"
        "            let mut line_start = 0u32;\n"
        "            let mut line_width = 0i32;\n"
        "            let mut line_height = 0i32;\n"
        "            let mut line_object_fs = 0.0f64;\n"
        "\n"
        "            for (utf16_start, (ctrl_width, ctrl_height)) in inline_sizes.iter().copied() {\n"
        "                if line_width > 0 && line_width + ctrl_width > max_line_width {\n"
        "                    line_specs.push((line_start, line_width, line_height, line_object_fs));\n"
        "                    line_start = utf16_start;\n"
        "                    line_width = 0;\n"
        "                    line_height = 0;\n"
        "                    line_object_fs = 0.0;\n"
        "                }\n"
        "                line_width += ctrl_width;\n"
        "                line_height = line_height.max(ctrl_height);\n"
        "                line_object_fs = line_object_fs.max(font_size_at(utf16_start));\n"
        "            }\n"
        "            line_specs.push((line_start, line_width, line_height, line_object_fs));\n",
    ),
    (
        REL,
        "            for (line_idx, (start_pos, _line_width, height_hwp)) in\n"
        "                line_specs.into_iter().enumerate()\n"
        "            {\n",
        "            for (line_idx, (start_pos, _line_width, height_hwp, object_fs)) in\n"
        "                line_specs.into_iter().enumerate()\n"
        "            {\n",
    ),
    (
        REL,
        "                    .map(|style| style.font_size)\n"
        "                    .unwrap_or(0.0);\n"
        "                let mut seg = make_line_seg(start_pos, control_font_size);\n",
        "                    .map(|style| style.font_size)\n"
        "                    .unwrap_or(0.0)\n"
        "                    .max(object_fs);\n"
        "                let mut seg = make_line_seg(start_pos, control_font_size);\n",
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
            sys.exit(f"{rel}: 자리 {n}곳 — {find[:50]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel)


if __name__ == "__main__":
    main()
