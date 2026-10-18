"""개발용: 글머리표 문단의 가로 배치를 한/글 실측(exp/make_bulletindent.py, 8종)에 맞춘다.

    python apply_bullet_place.py [--revert]

한/글(d010 문단 모양 72 사본, 들여쓰기 -1500/-616/0/500 x 자동 내어쓰기 켬/끔):
- 표식 자리는 글자 폭이 아니라 bullet-advance 규칙(표식 칸 + 글자 크기 x 본문과의 거리 %) — 11pt 전각, 20% 면 1320.
- 자동 내어쓰기 켬: 첫 줄 글 = 여백 + 자리, 이어지는 줄 = 여백 + 자리 + 내어쓰기.
- 자동 내어쓰기 끔: 첫 줄 글 = 여백 + max(들여쓰기, 0) + 자리, 이어지는 줄 = 여백 + max(-들여쓰기, 0) (표식 자리 없음).
엔진은 ① 그릴 때 표식 자리를 「○ 」 글자 폭(13pt 글자 + 빈칸 = 18.9pt)으로 재 첫 줄 글이 5~6pt 오른쪽, ② 이어지는 줄을 자동
내어쓰기와 상관없이 그만큼 밀었다(끔에서 +18.9pt), ③ 줄 나눔은 자동 내어쓰기를 끈 글머리표의 자리를 빼지 않았다. d010 p8 이
한 글자 넘쳐 쪽이 늘었다. 자동 내어쓰기 + 양수 들여쓰기(한/글: 첫 줄은 들여쓰지 않고 이어지는 줄 = 여백 + 자리 - 들여쓰기)는 드물어
종전대로 둔다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx bullet-place]"
LB = "renderer/composer/line_breaking.rs"
PL = "renderer/layout/paragraph_layout.rs"

EDITS = [
    (
        LB,
        "fn claude_bullet_advance_hwp(para: &Paragraph, styles: &ResolvedStyleSet) -> Option<i32> {\n",
        f"""fn claude_bullet_advance_hwp(para: &Paragraph, styles: &ResolvedStyleSet) -> Option<i32> {{
    // {TAG} 자동 내어쓰기를 켠 글머리표만(모든 줄을 좁힌다). 끈 글머리표는 번호 문단처럼 첫 줄만 좁힌다(reflow)
    claude_bullet_head_hwp(para, styles)
        .filter(|(_, auto)| *auto)
        .map(|(advance, _)| advance)
}}

/// {TAG} 글머리표 문단의 (표식 자리 HWPUNIT, 자동 내어쓰기). 그리기(paragraph_layout)도 같은 값을 쓴다
pub(crate) fn claude_bullet_head_hwp(
    para: &Paragraph,
    styles: &ResolvedStyleSet,
) -> Option<(i32, bool)> {{
""",
    ),
    (
        LB,
        """    if !auto_indent {
        return None;
    }
    let char_style_id = if (bullet.char_shape_id as usize) < styles.char_styles.len() {
""",
        """    // [claude-hwpx bullet-place] 자동 내어쓰기를 끈 글머리표도 자리를 돌려준다(종전 None)
    let char_style_id = if (bullet.char_shape_id as usize) < styles.char_styles.len() {
""",
    ),
    (
        LB,
        """    Some(advance + i32::from(bullet.width_adjust))
}
""",
        """    Some((advance + i32::from(bullet.width_adjust), auto_indent))
}
""",
    ),
    (
        LB,
        "        match claude_number_head_hwp(para, styles).filter(|(advance, _)| *advance > 0 && *advance < seg_width_hwp) {\n",
        "        match claude_number_head_hwp(para, styles)\n"
        "            .or_else(|| claude_bullet_head_hwp(para, styles).filter(|(_, auto)| !*auto))\n"
        "            .filter(|(advance, _)| *advance > 0 && *advance < seg_width_hwp)\n"
        "        {\n",
    ),
    (
        "renderer/composer.rs",
        # 기존 패치 load-picture-band-export 가 내보내기 목록 글을 표지로 쓰므로 그 목록은 건드리지 않고 따로 내보낸다
        "#[cfg(test)]\nmod lineseg_compare_tests;\n",
        "// [claude-hwpx bullet-place] 그리기도 글머리표 자리를 같은 규칙으로 쓴다\n"
        "pub(crate) use line_breaking::claude_bullet_head_hwp;\n\n"
        "#[cfg(test)]\nmod lineseg_compare_tests;\n",
    ),
    (
        PL,
        """        // 배경/테두리 렌더링을 위한 시작 위치 기록
        // 문단 경계 = 이전 문단 끝 = y_start (spacing_before 적용 전)
""",
        f"""        // {TAG} 글머리표 표식 자리는 글자 폭이 아니라 한/글 규칙(표식 칸 + 본문과의 거리, 줄 나눔과 같은 값)이다.
        // 이어지는 줄은 자동 내어쓰기일 때만 그만큼 민다(끄면 들여쓰기만). 자동 내어쓰기 + 양수 들여쓰기는 종전대로
        let claude_bullet: Option<(f64, bool)> = para.and_then(|p| {{
            let (advance, auto) = crate::renderer::composer::claude_bullet_head_hwp(p, styles)?;
            let indent = styles
                .para_styles
                .get(p.para_shape_id as usize)
                .map(|s| s.indent)
                .unwrap_or(0.0);
            (advance > 0 && !(auto && indent > 0.0)).then(|| (hwpunit_to_px(advance, self.dpi), auto))
        }});
        let numbering_width = match claude_bullet {{
            Some((advance, _)) if numbering_width > 0.0 => advance,
            _ => numbering_width,
        }};
        let claude_cont_offset = match claude_bullet {{
            Some((advance, true)) => advance,
            Some((_, false)) => 0.0,
            None => numbering_width,
        }};

        // 배경/테두리 렌더링을 위한 시작 위치 기록
        // 문단 경계 = 이전 문단 끝 = y_start (spacing_before 적용 전)
""",
    ),
    (
        PL,
        """            // 번호/글머리표 마커: 모든 줄에서 마커 폭만큼 가용폭 차감 (행잉 인덴트)
            let num_offset = if numbering_width > 0.0 {
                numbering_width
            } else {
                0.0
            };
""",
        """            // 번호/글머리표 마커: 모든 줄에서 마커 폭만큼 가용폭 차감 (행잉 인덴트)
            // [claude-hwpx bullet-place] 첫 줄은 표식 자리, 이어지는 줄은 내어쓰기 몫(글머리표는 자동 내어쓰기일 때만)
            let num_offset = if line_idx == start_line && start_line == 0 {
                numbering_width
            } else {
                claude_cont_offset
            };
""",
    ),
    (
        PL,
        """                    line_node.children.push(num_node);
                    x += num_width;
""",
        """                    line_node.children.push(num_node);
                    // [claude-hwpx bullet-place] 글머리표는 그린 글자 폭이 아니라 표식 자리만큼 나아간다
                    x += if claude_bullet.is_some() { numbering_width } else { num_width };
""",
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
