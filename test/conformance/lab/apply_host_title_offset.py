"""개발용: HWPX 에서 글 있는 문단의 자리 차지 표 오프셋이 첫 줄 높이보다 작으면 글줄을 표 위가 아니라 아래에 둔다.

    python apply_host_title_offset.py [--revert]

사본 실험(exp/make_hostline.py, d034 p65 「가. 목적」 + 오른쪽 표, 줄 1300 + 간격 1040, 표 바깥 높이 = 오프셋 + 3311):
오프셋 0, 196, 1000, 1016, 1017, 1299 는 글줄이 표 아래(문단 윗변 + 표 바깥 높이), 1300, 1301, 1900 ~ 5000 은 글줄이 표 위(+0).
경계는 「오프셋 ≥ 첫 줄 높이(vertsize, 줄 간격과 바깥 여백 제외)」. 그리기의 제목 줄 예약(Task #2711)은 오프셋 > 0 이면 늘 글줄을
표 위에 두고 표를 그 아래로 밀었다(d034 5쪽 「가. 목적」 −46.7px, 뒤 글 −17.3px). 오프셋이 첫 줄 높이보다 작으면 예약하지 않는다 —
표가 문단 위를 덮어 글이 표 아래로 밀리는 오프셋 0 경로와 같아진다(실험 오프셋 0 은 이미 한/글과 같다).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx host-title-offset]"

EDITS = [
    (
        "renderer/layout.rs",
        "                let table_y_start = if is_current_visible_para_float\n"
        "                    && signed_hwpunit(t.common.vertical_offset) > 0\n"
        "                {\n"
        "                    let host_line_px = para\n",
        "                let table_y_start = if is_current_visible_para_float\n"
        "                    && signed_hwpunit(t.common.vertical_offset) > 0\n"
        f"                    // {TAG} HWPX 는 오프셋이 첫 줄 높이보다 작으면 글줄이 표 아래로 간다(사본 실험 경계 1299/1300)\n"
        "                    && !(self.profile.get().hwpx_container()\n"
        "                        && para.line_segs.first().is_some_and(|s| {\n"
        "                            signed_hwpunit(t.common.vertical_offset) < s.line_height\n"
        "                        }))\n"
        "                {\n"
        "                    let host_line_px = para\n",
    ),
    (
        "renderer/layout.rs",
        "                y_offset = if is_current_visible_para_float {\n"
        "                    let mut flow_y = if signed_hwpunit(t.common.vertical_offset) > 0 {\n",
        "                y_offset = if is_current_visible_para_float {\n"
        f"                    // {TAG} 오프셋이 첫 줄 높이보다 작으면 글줄이 표 아래로 가므로 흐름도 표 바닥에서 잇는다(오프셋 0 분기)\n"
        "                    let claude_text_below_table = self.profile.get().hwpx_container()\n"
        "                        && para.line_segs.first().is_some_and(|s| {\n"
        "                            signed_hwpunit(t.common.vertical_offset) < s.line_height\n"
        "                        });\n"
        "                    let mut flow_y = if signed_hwpunit(t.common.vertical_offset) > 0\n"
        "                        && !claude_text_below_table\n"
        "                    {\n",
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
