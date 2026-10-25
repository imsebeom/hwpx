"""개발용: 글자처럼 취급 표의 칸 문단에 줄 배치가 하나라도 빠졌으면 선언 높이로 표를 줄이지 않는다(내용대로 키운다).

    python apply_tac_stale_grow.py [--revert]

근거(한국문화 1단원 삽입본 1쪽 pi=3 지도 표, 한/글 2024 PDF): 2×2 글자처럼 취급 표, 선언 25487(339.8px),
지도 칸에 그림(21423)과 빈 문단 둘(하나는 줄 배치 없음, 하나는 그림 넣기 전 낡은 줄 배치). 내용으로 잰 행은 332.1px(칸 선언 307.6).
한/글은 표를 364.0px 로 그린다(행 331.8). 엔진은 칸 문단이 모두 줄 배치가 없을 때만 「생성기 표」로 보고 키웠고,
섞인 표는 선언 339.8px 로 지도 행을 눌렀다. 줄 배치가 빠진 문단이 있으면 표 선언은 내용이 바뀌기 전 값이다
(stale-declared-grow 와 같은 판정, 한국문화 12단원).
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx tac-stale-grow]"
F = "renderer/height_measurer.rs"

EDITS = [
    (
        F,
        (
            "        let generator_restated_height = !self.is_native_hwp5\n"
            "            && table.cells.iter().all(|c| {\n"
            "                c.paragraphs.iter().all(crate::renderer::para_has_no_stored_line_segs)\n"
            "            });\n"
        ),
        (
            "        let generator_restated_height = !self.is_native_hwp5\n"
            "            && (table.cells.iter().all(|c| {\n"
            "                c.paragraphs.iter().all(crate::renderer::para_has_no_stored_line_segs)\n"
            "            })\n"
            f"                // {TAG} 줄 배치가 빠진 칸 문단이 든 칸의 행이 칸 선언보다 커졌으면 그 내용은 선언을 적은 뒤에 바뀐 것이다\n"
            "                // (한국문화 1단원 지도 표: 한/글 364px. 그 칸이 선언 안에 들고 다른 행만 넘치면 한/글은 선언대로, 회귀 r12)\n"
            "                || (table.common.treat_as_char\n"
            "                    && table.cells.iter().any(|c| {\n"
            "                        let r = c.row as usize;\n"
            "                        c.row_span == 1\n"
            "                            && r < row_heights.len()\n"
            "                            && c.height < 0x8000_0000\n"
            "                            && c.paragraphs.iter().any(crate::renderer::para_has_no_stored_line_segs)\n"
            "                            && row_heights[r] > hwpunit_to_px(c.height as i32, self.dpi) + 0.5\n"
            "                    })));\n"
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
