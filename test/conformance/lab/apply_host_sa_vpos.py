"""개발용: HWPX 에서 자리 차지 표(문단 기준) 호스트 문단의 그리기 위치에 앞 문단 아래 간격을 넣는다.

    python apply_host_sa_vpos.py [--revert]

높이 커서(vpos_adjust)는 현재 문단이 자리 차지 표 호스트이면 호스트 vpos 에 표 높이가 들 수 있다고 보고(PR #1088) 앞 문단 줄 끝
(vpos + 줄 높이 + 줄 간격)을 쓴다. 그러면 앞 문단 아래 간격이 빠진다. 한/글 새 조판 d124 p27(빈 문단, 표 24300): 호스트 줄
16246 = p26 끝 15746 + 아래 간격 500, 표 위 괘선 310.7px, 엔진 304.4px(6.3 위). 조판(합성 vpos 87045)은 이미 맞다.
호스트 vpos 가 「앞 문단 끝 + 앞 아래 간격 + 자기 위 간격」을 넘지 않으면 표 높이를 담지 않은 것이니 그 vpos 를 쓴다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx host-sa-vpos]"

EDITS = [
    (
        "renderer/height_cursor.rs",
        "            Some(v) if v > seg.vertical_pos && !curr_has_topbottom_para_table => v,\n"
        "            _ => prev_vpos_end,\n"
        "        };\n",
        "            Some(v) if v > seg.vertical_pos && !curr_has_topbottom_para_table => v,\n"
        f"            // {TAG} HWPX 자리 차지 표 호스트의 vpos 가 앞 문단 끝 + 앞 아래 간격 + 자기 위 간격 안이면 표 높이를\n"
        "            // 담지 않은 호스트 윗변이다 — 앞 문단 아래 간격을 잃지 않게 그대로 쓴다(d124 p27)\n"
        "            Some(v)\n"
        "                if v > prev_vpos_end\n"
        "                    && curr_has_topbottom_para_table\n"
        "                    && self.suppress_hwpx_stale_forward\n"
        "                    && {\n"
        "                        let px_to_hu = |px: f64| (px.max(0.0) * 7200.0 / self.dpi).round() as i32;\n"
        "                        let prev_sa_hu = paragraphs\n"
        "                            .get(prev_pi)\n"
        "                            .and_then(|p| styles.para_styles.get(p.para_shape_id as usize))\n"
        "                            .map(|ps| px_to_hu(ps.spacing_after))\n"
        "                            .unwrap_or(0);\n"
        "                        let curr_sb_hu = paragraphs\n"
        "                            .get(item_para)\n"
        "                            .and_then(|p| styles.para_styles.get(p.para_shape_id as usize))\n"
        "                            .map(|ps| px_to_hu(ps.spacing_before))\n"
        "                            .unwrap_or(0);\n"
        "                        v <= prev_vpos_end + prev_sa_hu + curr_sb_hu + 1\n"
        "                    } =>\n"
        "            {\n"
        "                v\n"
        "            }\n"
        "            _ => prev_vpos_end,\n"
        "        };\n",
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
