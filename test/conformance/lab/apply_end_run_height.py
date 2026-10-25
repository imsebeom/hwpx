"""개발용: 문단 마지막 줄의 높이에 문단 끝 빈 run(문단 부호 글자 모양)의 크기를 넣는다.

    python apply_end_run_height.py [--revert]

근거:
- 정답본 327개 한/글 재저장본(scratchpad harvest_endrun.py): 글이 든 한 줄 문단 가운데 끝 run 이 글 없는 run 이고
  그 크기가 글 run 가장 큰 크기보다 큰 1,330건에서 줄 높이(vertsize)가 끝 run 크기와 같은 것 1,204건, 글 run 크기와 같은 것 0건
  (나머지 126건은 다른 값)
- 한국문화 1단원 1쪽 제목(글 20pt, 끝 빈 run 25pt): 한/글 PDF 기준선이 본문 위에서 28.2px(= 2500 x 0.85),
  엔진은 22.7px(2000 기준)이라 쪽 전체가 5.5px 위로 올라가 있었다
엔진은 줄에 든 글자의 크기만 셌다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx end-run-height]"
F = "renderer/composer/line_breaking.rs"

EDITS = [
    (
        F,
        (
            "        let fs = if lb.max_font_size > 0.0 {\n"
            "            lb.max_font_size\n"
            "        } else {\n"
            "            12.0\n"
            "        };\n"
            "        let mut text_seg = make_line_seg(utf16_start, fs);\n"
        ),
        (
            "        let fs = if lb.max_font_size > 0.0 {\n"
            "            lb.max_font_size\n"
            "        } else {\n"
            "            12.0\n"
            "        };\n"
            f"        // {TAG} 마지막 줄은 문단 끝 빈 run(문단 부호의 글자 모양)의 크기도 센다\n"
            "        // (정답본 1,330건 중 1,204건이 끝 run 크기, 글 run 크기는 0건. 한국문화 1단원 제목 25pt)\n"
            "        let fs = if line_idx + 1 == line_breaks.len() && text_len > 0 {\n"
            "            let text_end_u16 = char_index_to_utf16_offset(para, text_len);\n"
            "            para.char_shapes\n"
            "                .iter()\n"
            "                .filter(|c| c.start_pos >= text_end_u16)\n"
            "                .filter_map(|c| styles.char_styles.get(c.char_shape_id as usize))\n"
            "                .map(|style| style.font_size)\n"
            "                .fold(fs, f64::max)\n"
            "        } else {\n"
            "            fs\n"
            "        };\n"
            "        let mut text_seg = make_line_seg(utf16_start, fs);\n"
        ),
    ),
]


def main():
    revert = "--revert" in sys.argv
    for rel, find, repl in EDITS:
        if revert:
            find, repl = repl, find
        f = SRC / rel
        raw = f.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        a, b = find.replace("\n", nl), repl.replace("\n", nl)
        if raw.count(a) != 1:
            sys.exit(f"{rel}: 고칠 자리를 하나로 못 찾았다({raw.count(a)})")
        f.write_bytes(raw.replace(a, b).encode("utf-8"))
    print("되돌림" if revert else "고침", len(EDITS))


if __name__ == "__main__":
    main()
