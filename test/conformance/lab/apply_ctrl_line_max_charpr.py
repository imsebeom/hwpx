"""개발용: 글 없는 줄(글자처럼 취급 개체만 든 줄, 빈 문단)의 줄 높이와 간격을 그 줄에 걸친 run 가운데 가장 큰 글자 크기로 셈한다.

    python apply_ctrl_line_max_charpr.py [--revert]

근거(2026-10-18 정답본 한/글 줄 기록):
- secpr_engine.py: 첫 run 에 구역 정의만 있고 뒤 run 에 글자처럼 취급 표가 든 첫 문단 35건 가운데 줄 높이는 같고 간격만 어긋난 것이
  14건이다. 한/글 간격은 모두 줄의 run 가운데 가장 큰 크기 기준이다(d001 1900, 1900, 2200 → 1320, d095 끝 빈 run 1500 → 900,
  d272 500, 500, 1000, 2400 → 1440, d345 150% 1700 → 852). 엔진은 줄 시작(구역 정의 run) 크기를 써서 간격이 작았다.
- harvest_emptyruns.py: 글도 개체도 없는 문단에 크기가 다른 run 이 여럿이면 줄 높이가 가장 큰 run 을 따른다(11건 중 10건,
  첫 run 7건, 예외 d174 [1500, 1500, 1000] → 1000).
엔진은 개체만 든 줄은 줄 시작 run, 빈 문단은 첫 run 크기를 썼다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx ctrl-line-max-charpr]"

EDITS = [
    (
        "renderer/composer/line_breaking.rs",
        "            let mut new_line_segs = Vec::with_capacity(line_specs.len());\n"
        "            for (line_idx, (start_pos, _line_width, height_hwp)) in\n"
        "                line_specs.into_iter().enumerate()\n"
        "            {\n",
        "            let mut new_line_segs = Vec::with_capacity(line_specs.len());\n"
        f"            // {TAG} 줄마다 다음 줄 시작(마지막 줄은 문단 끝까지)\n"
        "            let claude_line_ends: Vec<u32> = line_specs.iter().skip(1).map(|spec| spec.0).collect();\n"
        "            for (line_idx, (start_pos, _line_width, height_hwp)) in\n"
        "                line_specs.into_iter().enumerate()\n"
        "            {\n",
    ),
    (
        "renderer/composer/line_breaking.rs",
        "                let control_font_size = para\n"
        "                    .char_shapes\n"
        "                    .iter()\n"
        "                    .rev()\n"
        "                    .find(|c| c.start_pos <= start_pos)\n"
        "                    .or_else(|| para.char_shapes.first())\n"
        "                    .and_then(|c| styles.char_styles.get(c.char_shape_id as usize))\n"
        "                    .map(|style| style.font_size)\n"
        "                    .unwrap_or(0.0);\n",
        "                let control_font_size = para\n"
        "                    .char_shapes\n"
        "                    .iter()\n"
        "                    .rev()\n"
        "                    .find(|c| c.start_pos <= start_pos)\n"
        "                    .or_else(|| para.char_shapes.first())\n"
        "                    .and_then(|c| styles.char_styles.get(c.char_shape_id as usize))\n"
        "                    .map(|style| style.font_size)\n"
        "                    .unwrap_or(0.0);\n"
        f"                // {TAG} 한/글은 그 줄에 걸친 run(구역 정의만 든 run, 끝 빈 run 포함) 가운데 가장 큰 크기로 셈한다\n"
        "                // (secpr_engine.py: d001 1900, 1900, 2200 → 간격 1320, d095 끝 빈 run 1500 → 900)\n"
        "                let line_end = claude_line_ends.get(line_idx).copied().unwrap_or(u32::MAX);\n"
        "                let control_font_size = para\n"
        "                    .char_shapes\n"
        "                    .iter()\n"
        "                    .filter(|c| c.start_pos >= start_pos && c.start_pos < line_end)\n"
        "                    .filter_map(|c| styles.char_styles.get(c.char_shape_id as usize))\n"
        "                    .map(|style| style.font_size)\n"
        "                    .fold(control_font_size, f64::max);\n",
    ),
    (
        "renderer/composer/line_breaking.rs",
        "            let font_size = para\n"
        "                .char_shapes\n"
        "                .first()\n"
        "                .and_then(|char_shape| styles.char_styles.get(char_shape.char_shape_id as usize))\n"
        "                .or_else(|| para.char_shapes.is_empty().then(|| styles.char_styles.first()).flatten())\n"
        "                .map(|style| style.font_size)\n"
        "                .unwrap_or(12.0);\n",
        "            let font_size = para\n"
        "                .char_shapes\n"
        "                .first()\n"
        "                .and_then(|char_shape| styles.char_styles.get(char_shape.char_shape_id as usize))\n"
        "                .or_else(|| para.char_shapes.is_empty().then(|| styles.char_styles.first()).flatten())\n"
        "                .map(|style| style.font_size)\n"
        "                .unwrap_or(12.0);\n"
        f"            // {TAG} run 이 여럿이면 가장 큰 크기(harvest_emptyruns.py: 11건 중 10건, 첫 run 은 7건)\n"
        "            let font_size = para\n"
        "                .char_shapes\n"
        "                .iter()\n"
        "                .filter_map(|c| styles.char_styles.get(c.char_shape_id as usize))\n"
        "                .map(|style| style.font_size)\n"
        "                .fold(font_size, f64::max);\n",
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
