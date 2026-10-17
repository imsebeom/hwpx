"""개발용: 줄은 앞 줄 마지막 글자 바로 다음 위치에서 시작한다(줄 경계의 조판 부호를 새 줄에 둔다).

    python apply_break_ctrl_start.py [--revert]

근거(정답본): 줄 경계에 조판 부호(하이퍼링크 시작 등, UTF-16 8칸)가 끼면 한/글 줄 기록은 새 줄을 그 부호 위치에서 시작한다.
d309 칸 121 「2024. 11.<lineBreak/>」 뒤 하이퍼링크: 한/글 50, 엔진 58. 엔진은 새 줄 첫 글자의 위치를 써서 부호가 앞 줄 끝에 붙었다.
강제 줄바꿈 뒤로만 좁히면 2줄, 모든 줄 경계에 쓰면 7줄이 맞고 새로 틀린 줄은 0(네이티브 채점 327문서).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx break-ctrl-start]"
LB = "renderer/composer/line_breaking.rs"

HELPER = (
    f"/// {TAG} 줄 시작의 UTF-16 위치 = 앞 줄 마지막 글자 바로 다음. 줄 경계의 조판 부호(하이퍼링크 시작 등)는 새 줄에 둔다\n"
    "/// (한/글 2024 줄 기록, d309: 강제 줄바꿈 뒤 하이퍼링크 부호가 있으면 새 줄이 부호 위치에서 시작).\n"
    "fn claude_line_start_utf16(para: &Paragraph, char_index: usize) -> u32 {\n"
    "    let own = char_index_to_utf16_offset(para, char_index);\n"
    "    if char_index > 0 {\n"
    "        if let (Some(prev), Some(ch)) = (para.char_offsets.get(char_index - 1), para.text.chars().nth(char_index - 1)) {\n"
    "            return (*prev + ch.len_utf16() as u32).min(own);\n"
    "        }\n"
    "    }\n"
    "    own\n"
    "}\n\n"
)

EDITS = [
    (
        LB,
        "fn char_index_to_utf16_offset(para: &Paragraph, char_index: usize) -> u32 {\n",
        HELPER
        + "fn char_index_to_utf16_offset(para: &Paragraph, char_index: usize) -> u32 {\n",
    ),
    (
        LB,
        "                    } else {\n                        char_index_to_utf16_offset(para, line.start_idx)\n                    };\n                    let text_end",
        "                    } else {\n                        claude_line_start_utf16(para, line.start_idx)\n                    };\n                    let text_end",
    ),
    (
        LB,
        "            0 // 첫 번째 줄의 text_start는 항상 0 (문단 시작)\n        } else {\n            char_index_to_utf16_offset(para, lb.start_idx)\n",
        "            0 // 첫 번째 줄의 text_start는 항상 0 (문단 시작)\n        } else {\n            claude_line_start_utf16(para, lb.start_idx)\n",
    ),
    (
        LB,
        "                    text_start: if index == 0 {\n                        0\n                    } else {\n                        char_index_to_utf16_offset(para, line.start_idx)\n",
        "                    text_start: if index == 0 {\n                        0\n                    } else {\n                        claude_line_start_utf16(para, line.start_idx)\n",
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
