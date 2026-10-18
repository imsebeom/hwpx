"""개발용: 쪽 끝에서 행 안 분할이 안 되는(한 줄짜리 등) 행도 보이는 내용이 남은 자리에 들어가면 그 쪽에 둔다(CELL 표, HWPX).

    python apply_row_visible_fit.py [--revert]

근거(2026-10-18 d194 한/글 PDF 괘선, 쪽번호시험 사본 실험 scratchpad make_rowfit2.py, make_rowfit3.py):
- d194 49행 CELL 표(p90, 행 23.3px)를 5쪽 끝에서 가를 때 한/글은 14번째 행을 18.2px 만 담고 다음 행부터 6쪽으로 넘긴다.
- 32px 행(칸 선언 높이 2400, 칸 여백 142, 줄 1000 + 간격 300, 가운데 정렬) 앞에 얇은 문단을 넣어 쪽 끝 남은 자리를 줄여 가니
  남은 자리 17.42px 까지는 그 행을 담고(본문 바닥까지 잘라 그림) 17.1px 에서 넘긴다. 위 여백 + 글 높이 + 아래 여백
  = 142 + 1000 + 142 = 1284 HWPUNIT(17.12px)와 같다. 세로 정렬과 선언 행 높이와는 무관하다(d069 의 17.1px 도 넘김).
엔진은 한 줄짜리 행을 「분할 불가」로 보고 통째로 다음 쪽에 넘겨 d194 가 한 쪽 많았다.
필요 높이 = 위 여백 + 줄들(높이 + 간격) - 마지막 줄 간격 + 아래 여백. 개체가 든 칸은 넣지 않는다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx row-visible-fit]"

EDITS = [
    (
        "renderer/typeset.rs",
        "            if !splittable {\n"
        "                // [#2236 진단] 분할 불가 정지 — 동작 불변.\n",
        f"            // {TAG} 분할 불가 행도 위 여백 + 줄들(마지막 줄 간격 빼고) + 아래 여백이 남은 자리에 들어가면 이 쪽에 남은 높이로 둔다\n"
        "            // (쪽번호시험 사본 실험: 32px 행이 남은 17.42px 에서 담기고 17.1px 에서 넘어간다 = 142 + 1000 + 142. d194 도 같은 규칙)\n"
        "            if !splittable\n"
        "                && st.profile.hwpx_container()\n"
        "                && mt.allows_row_break_split()\n"
        "                && r > cursor_row\n"
        "                && row_start_cut.is_empty()\n"
        "                && !rowspan_touched[r]\n"
        "            {\n"
        "                let rest = (avail_for_rows - consumed - cs_before).max(0.0);\n"
        "                let visible = table\n"
        "                    .cells\n"
        "                    .iter()\n"
        "                    .filter(|cell| cell.row as usize == r && cell.row_span == 1)\n"
        "                    .map(|cell| {\n"
        "                        if cell.paragraphs.iter().any(|p| !p.controls.is_empty() || p.line_segs.is_empty()) {\n"
        "                            return f64::INFINITY;\n"
        "                        }\n"
        "                        let pad = cell.effective_padding_in(table);\n"
        "                        let lines: i32 = cell\n"
        "                            .paragraphs\n"
        "                            .iter()\n"
        "                            .flat_map(|p| p.line_segs.iter())\n"
        "                            .map(|s| s.line_height + s.line_spacing.max(0))\n"
        "                            .sum();\n"
        "                        let last_ls = cell\n"
        "                            .paragraphs\n"
        "                            .last()\n"
        "                            .and_then(|p| p.line_segs.last())\n"
        "                            .map(|s| s.line_spacing.max(0))\n"
        "                            .unwrap_or(0);\n"
        "                        hwpunit_to_px(pad.top as i32 + lines - last_ls + pad.bottom as i32, self.dpi)\n"
        "                    })\n"
        "                    .fold(0.0f64, f64::max);\n"
        "                if visible > 0.0 && visible.is_finite() && visible <= rest + 0.01 {\n"
        "                    consumed += cs_before + rest;\n"
        "                    r += 1;\n"
        "                    end_row = r;\n"
        "                    end_row_height_override = Some(rest);\n"
        "                    continue;\n"
        "                }\n"
        "            }\n"
        "            if !splittable {\n"
        "                // [#2236 진단] 분할 불가 정지 — 동작 불변.\n",
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
