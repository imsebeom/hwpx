"""개발용: 글 줄 뒤에 붙은 어울림 표(Square)는 「max(글 줄, 오프셋 + 바깥 여백 위 + 선언 높이 + 바깥 여백 아래)」 만큼 전진한다.

    python apply_para_float_text_host.py [--revert]

근거(d160 p3, p6): 「1. 기본 정보」 글 줄 뒤에 어울림 표(vertRelTo=PARA, vertOffset 1901)가 붙은 문단에서 한/글은 다음 문단을
8569 + 1901 + 283 + 9258 + 283 = 20294 에서 시작한다. 엔진의 어울림 분기는 「오프셋 + 표 전체 높이」를 썼는데 표 전체 높이가
바깥 여백 대신 문단 줄 간격(780)을 품고 있어 214 HU 더 내려갔고(p6 은 715), 같은 서식의 d160, d204, d251 이 한 쪽씩 늘었다.
HWPX 이고 저장 줄 배치가 없는 문단(에디터가 만든 문서, 채점의 줄 배치를 지운 문서)만 바꾼다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx para-float-text-host]"

EDITS = [
    (
        "renderer/typeset.rs",
        "        if is_wrap_around_table && pre_height > 0.0 {\n"
        "            let v_off_px = crate::renderer::hwpunit_to_px(vertical_offset as i32, self.dpi);\n"
        "            let table_bottom = v_off_px + table_total_height;\n",
        "        if is_wrap_around_table && pre_height > 0.0 {\n"
        "            let v_off_px = crate::renderer::hwpunit_to_px(vertical_offset as i32, self.dpi);\n"
        f"            // {TAG} 한/글은 표 바닥을 오프셋 + 바깥 여백 위 + 선언 높이 + 바깥 여백 아래로 잡는다(d160 p3: 1901+283+9258+283).\n"
        "            // 표 전체 높이(table_total_height)는 바깥 여백 대신 문단 줄 간격을 품고 있어 그만큼 내려갔다\n"
        "            let table_bottom = if st.profile.hwpx_stored_layout()\n"
        "                && crate::renderer::para_has_no_stored_line_segs(para)\n"
        "                && table.common.height > 0\n"
        "            {\n"
        "                v_off_px\n"
        "                    + hwpunit_to_px(\n"
        "                        i32::from(table.outer_margin_top)\n"
        "                            + table.common.height as i32\n"
        "                            + i32::from(table.outer_margin_bottom),\n"
        "                        self.dpi,\n"
        "                    )\n"
        "            } else {\n"
        "                v_off_px + table_total_height\n"
        "            };\n",
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
