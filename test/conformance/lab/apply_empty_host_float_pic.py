"""개발용: 글 없는 본문 문단에 위아래 배치 그림, 도형 하나만 있으면 다음 문단을 max(빈 문단 높이, 개체 아래 - 다음 문단 위 간격)에서 시작한다.

    python apply_empty_host_float_pic.py [--revert]

근거(2026-10-18 정답본 한/글 줄 기록, harvest_floatpic.py): 글 없는 문단에 문단 기준 위아래 배치(글자처럼 취급 아님) 개체 하나만
있을 때 다음 문단 vpos - 이 문단 vpos = 세로 오프셋 + 바깥 여백 위아래 + 개체 높이 - 이 문단 위 간격이다(그림 6건 모두, 표 241건).
개체 위치가 문단 위 간격을 빼기 전 시작점 기준이고, 다음 문단의 위 간격은 개체 아래와 겹쳐 사라진다. d266 p7: 21490 - 300 + 362 + 18778
= 40330(한/글 그대로). 엔진(그림, 도형 경로)은 빈 줄(위 간격 + 1100 + 660)에 개체 높이 + 아래 여백만 더해 세로 오프셋과 위 여백을 빼먹고
빈 줄을 겹치지 않아, d266 2쪽이 1700 HWPUNIT 늘었다. 표는 empty-host-block 이 이미 같은 식을 쓴다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx empty-host-float-pic]"

EDITS = [
    (
        "renderer/typeset.rs",
        "                            if let Some((obj_h, extra, h_left, h_right)) = pushdown_h {\n",
        "                            if let Some((obj_h, extra, h_left, h_right)) = pushdown_h {\n"
        f"                                // {TAG} 글 없는 문단의 개체 하나는 다음 문단을 max(빈 문단 높이, 오프셋 + 바깥 여백 + 높이 - 다음 문단 위 간격)에 둔다\n"
        "                                // (harvest_floatpic.py: 그림 6건 모두, 표 241건. d266 p7). 빈 문단 높이(위 간격 + 줄 + 아래 간격)는 이미 더했다\n"
        "                                let extra = if st.profile.hwpx_container()\n"
        "                                    && !para_has_visible_text(para)\n"
        "                                    && para.line_segs.len() <= 1\n"
        "                                    && para\n"
        "                                        .controls\n"
        "                                        .iter()\n"
        "                                        .filter(|c| matches!(c, Control::Picture(_) | Control::Shape(_) | Control::Table(_)))\n"
        "                                        .count()\n"
        "                                        == 1\n"
        "                                {\n"
        "                                    let cm = match ctrl {\n"
        "                                        Control::Picture(p) => Some(&p.common),\n"
        "                                        Control::Shape(s) => Some(s.common()),\n"
        "                                        _ => None,\n"
        "                                    };\n"
        "                                    cm.map(|cm| {\n"
        "                                        let obj_hu = signed_hwpunit(cm.vertical_offset).max(0)\n"
        "                                            + cm.margin.top as i32\n"
        "                                            + cm.height as i32\n"
        "                                            + cm.margin.bottom as i32;\n"
        "                                        let next_sb = paragraphs\n"
        "                                            .get(para_idx + 1)\n"
        "                                            .and_then(|np| styles.para_styles.get(np.para_shape_id as usize))\n"
        "                                            .map(|s| s.spacing_before)\n"
        "                                            .unwrap_or(0.0);\n"
        "                                        let own = styles.para_styles.get(para.para_shape_id as usize);\n"
        "                                        let host_px = own.map(|s| s.spacing_before + s.spacing_after).unwrap_or(0.0)\n"
        "                                            + para\n"
        "                                                .line_segs\n"
        "                                                .first()\n"
        "                                                .map(|s| hwpunit_to_px(s.line_height + s.line_spacing.max(0), self.dpi))\n"
        "                                                .unwrap_or(0.0);\n"
        "                                        (hwpunit_to_px(obj_hu, self.dpi) - next_sb - host_px).max(0.0)\n"
        "                                    })\n"
        "                                    .unwrap_or(extra)\n"
        "                                } else {\n"
        "                                    extra\n"
        "                                };\n",
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
