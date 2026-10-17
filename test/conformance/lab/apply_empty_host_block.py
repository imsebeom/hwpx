"""개발용: 빈 숙주 문단의 글 위아래 배치 표 하나가 쪽 흐름에서 차지하는 몫을 한/글 공식으로.

    python apply_empty_host_block.py [--revert]

근거(d329, 한/글 2024 정답본): 다음 문단 vertpos - 숙주 vertpos = 세로 오프셋 + 바깥 여백 위 + 선언 표 높이 + 바깥 여백 아래
(표 1: 204+283+10799+283 = 11569, 표 2: 0+283+47680+283 = 48246 — 둘 다 정확히 일치). 엔진은 이 분기에서 바깥 여백과
오프셋(extras)을 더하면서 표 몫으로 host 형식 높이(height_for_fit)를 써, 바깥 여백 등이 이중으로 들어가 쪽당 17px 넘쳤다
(d329 가 1쪽 → 2쪽).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx empty-host-block]"

EDITS = [
    (
        "renderer/typeset.rs",
        "            } else if let Some(extras_hu) = empty_host_physical_extras_hu {\n"
        "                st.current_height +=\n"
        "                    pre_height + table_total_height + hwpunit_to_px(extras_hu as i32, self.dpi);\n",
        "            } else if let Some(extras_hu) = empty_host_physical_extras_hu {\n"
        f"                // {TAG} 한/글 공식: 오프셋 + 바깥 여백 위아래(extras) + 선언 표 높이. host 형식 높이(table_total_height)는\n"
        "                // 바깥 여백 등을 이미 품고 있어 extras 와 겹쳤다(d329). 선언 높이가 없으면 종전 값.\n"
        "                let declared = hwpunit_to_px(table.common.height as i32, self.dpi);\n"
        "                let body = if declared > 1.0 { declared } else { table_total_height };\n"
        "                st.current_height += pre_height + body + hwpunit_to_px(extras_hu as i32, self.dpi);\n",
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
