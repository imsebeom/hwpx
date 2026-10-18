"""개발용: Word 호환 문서(targetProgram=MS_WORD + adjustLineheightToFont)의 비율 간격 줄 치수를 글꼴 파일의 세로 수치로 잡는다.

    python apply_word_compat_lineheight.py [--revert]

근거(2026-10-18 정답본 d076, d133 의 한/글 줄 기록):
- harvest_wordcompat.py: 한 줄 문단의 줄 높이가 글꼴마다 크기의 일정 배수다. 맑은 고딕 1.729~1.730, Pretendard 1.551.
  글꼴 파일 hhea 의 (ascender + descender + lineGap) / em(맑은 고딕 1.3301, Pretendard 1.1934)의 1.3배와 1 HWPUNIT 안에서 같다.
  기준선 = ascender x 크기 + (줄 높이 - hhea 높이) / 2(맑은 고딕 10pt 1288, Pretendard 14pt 1583 일치).
  비율 간격은 이 줄 높이에 기존 4 단위 반올림 식을 그대로 걸면 모두 맞는다(1729 160% → 1036, 2171 160% → 1300).
- harvest_wordmix.py: 문단 끝 빈 run 이 글보다 크면 줄 높이 = 빈 run 줄 높이 + 글의 아랫부분(줄 높이 - 기준선), 기준선은 빈 run 의 것
  (d133 126줄: 9pt 글 + 10pt 빈 run → 2126/1288, 10pt + 12pt → 2517/1546). 빈 run 이 작으면 무시한다(d076 24pt + 11pt → 3722/2714).
엔진은 Word 호환 문서도 크기 그대로(10pt → 1000) 줄을 만들어 d076, d133 이 한/글보다 짧았다.
세로 수치는 에디터가 글꼴 파일에서 읽어 폭 표와 함께 넘긴다(font-metrics.mjs `vm`). 수치가 없는 글꼴은 종전대로 둔다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx word-compat-lineheight]"

EDITS = [
    (
        "renderer/font_metrics_data.rs",
        "static CLAUDE_ZERO_MAP: [u8; 28] = [0; 28];\n",
        f"/// {TAG} 등록한 글꼴의 세로 수치(hhea ascender, descender, lineGap 을 em 으로 나눈 값). 보통 얼굴만 담는다\n"
        "static CLAUDE_RUNTIME_VM: OnceLock<std::sync::RwLock<HashMap<String, [f64; 3]>>> = OnceLock::new();\n"
        "\n"
        "/// 이 이름으로 등록한 글꼴의 세로 수치 [ascender, descender, lineGap](em 비율). Word 호환 문서의 줄 높이에 쓴다\n"
        "pub(crate) fn claude_font_vm(name: &str) -> Option<[f64; 3]> {\n"
        "    CLAUDE_RUNTIME_VM.get()?.read().ok()?.get(name).copied()\n"
        "}\n"
        "static CLAUDE_ZERO_MAP: [u8; 28] = [0; 28];\n",
    ),
    (
        "renderer/font_metrics_data.rs",
        '        let bold = face.get("bold").and_then(|v| v.as_bool()).unwrap_or(false);\n'
        "        let already = map\n",
        '        let bold = face.get("bold").and_then(|v| v.as_bool()).unwrap_or(false);\n'
        f"        // {TAG} 세로 수치는 폭 표와 따로 둔다(내장 표가 있어 폭 표를 건너뛰는 글꼴도 담는다)\n"
        "        if !bold {\n"
        '            let vm: Vec<f64> = face.get("vm").and_then(|v| v.as_array()).into_iter().flatten()\n'
        "                .filter_map(|x| x.as_i64())\n"
        "                .map(|x| x as f64 / em as f64)\n"
        "                .collect();\n"
        "            if vm.len() == 3 && vm[0] > 0.0 {\n"
        "                if let Ok(mut table) = CLAUDE_RUNTIME_VM.get_or_init(|| std::sync::RwLock::new(HashMap::new())).write() {\n"
        "                    table.entry(name.to_string()).or_insert([vm[0], vm[1], vm[2]]);\n"
        "                }\n"
        "            }\n"
        "        }\n"
        "        let already = map\n",
    ),
    (
        "renderer/style_resolver.rs",
        "    pub shade_color: ColorRef,\n}\n",
        "    pub shade_color: ColorRef,\n"
        f"    /// {TAG} Word 호환 문서(compatibleDocument targetProgram=MS_WORD 에 adjustLineheightToFont)의 글자 모양인가.\n"
        "    /// 비율 간격 줄의 높이를 글꼴 파일의 세로 수치로 잡는다(line_breaking `claude_word_line_metrics`). 문서 전체가 같은 값이다\n"
        "    pub claude_word_compat: bool,\n"
        "}\n",
    ),
    (
        "renderer/style_resolver.rs",
        "            font_family: String::new(),\n            font_families: Vec::new(),\n",
        "            font_family: String::new(),\n"
        f"            claude_word_compat: false, // {TAG}\n"
        "            font_families: Vec::new(),\n",
    ),
    (
        "renderer/style_resolver.rs",
        "    ResolvedCharStyle {\n        font_family,\n        font_families,\n        font_size,\n",
        "    ResolvedCharStyle {\n"
        "        font_family,\n"
        "        font_families,\n"
        "        font_size,\n"
        f"        // {TAG}\n"
        "        claude_word_compat: doc_info.hwpx_head_tail.as_deref().is_some_and(|tail| {\n"
        '            tail.contains("targetProgram=\\"MS_WORD\\"") && tail.contains("<hh:adjustLineheightToFont/>")\n'
        "        }),\n",
    ),
    (
        "renderer/composer/line_breaking.rs",
        "fn apply_inline_control_line_height(seg: &mut LineSeg, height_hwp: i32) {\n",
        f"/// {TAG} Word 호환 문서(targetProgram=MS_WORD + adjustLineheightToFont)의 줄 치수(HWPUNIT).\n"
        "/// 한/글은 글꼴 파일의 hhea 줄 높이로 줄을 만든다(lab harvest_wordcompat.py, d076, d133):\n"
        "/// 줄 높이 = 크기 x (ascender + descender + lineGap) / em x 1.3, 기준선 = ascender x 크기 + (줄 높이 - hhea 높이) / 2.\n"
        "/// 문단 끝 빈 run 이 글보다 크면 줄 높이는 「빈 run 줄 높이 + 글 아랫부분」, 기준선은 빈 run 의 것이다\n"
        "/// (harvest_wordmix.py, d133 126줄: 9pt 글 + 10pt 빈 run → 2126/1288). 그 줄의 비율 간격은 빈 run 줄 높이에 건다\n"
        "/// (d133 10pt 글 + 12pt 빈 run 160% → 2517 에 간격 1244 = 2076 기준). 반환 (줄 높이, 기준선, 간격 기준 높이).\n"
        "/// 글꼴 세로 수치가 없으면 None(종전대로).\n"
        "fn claude_word_line_metrics(\n"
        "    para: &Paragraph,\n"
        "    styles: &ResolvedStyleSet,\n"
        "    start_u16: u32,\n"
        "    end_u16: u32,\n"
        "    last_line: bool,\n"
        "    dpi: f64,\n"
        ") -> Option<(i32, i32, i32)> {\n"
        "    if !styles.char_styles.first().is_some_and(|style| style.claude_word_compat) {\n"
        "        return None;\n"
        "    }\n"
        "    let metric = |id: u32| -> Option<(f64, f64)> {\n"
        "        let style = styles.char_styles.get(id as usize)?;\n"
        "        let [asc, desc, gap] = crate::renderer::font_metrics_data::claude_font_vm(&style.font_family)?;\n"
        "        let size = style.font_size * 7_200.0 / dpi;\n"
        "        let ratio = asc + desc + gap;\n"
        "        let lh = size * ratio * 1.3;\n"
        "        Some((lh.round(), (asc * size + (lh - ratio * size) / 2.0).round()))\n"
        "    };\n"
        "    let refs = &para.char_shapes;\n"
        "    if para.text.is_empty() {\n"
        "        let (lh, bl) = metric(refs.first().map_or(0, |r| r.char_shape_id))?;\n"
        "        return Some((lh as i32, bl as i32, lh as i32));\n"
        "    }\n"
        "    let text_end = char_index_to_utf16_offset(para, para.text.chars().count());\n"
        "    let mut text: Option<(f64, f64)> = None;\n"
        "    for (i, r) in refs.iter().enumerate() {\n"
        "        let next = refs.get(i + 1).map_or(u32::MAX, |n| n.start_pos);\n"
        "        if r.start_pos < text_end && next > r.start_pos && r.start_pos < end_u16 && next > start_u16 {\n"
        "            let m = metric(r.char_shape_id)?;\n"
        "            text = Some(match text {\n"
        "                Some(t) if t.0 >= m.0 => t,\n"
        "                _ => m,\n"
        "            });\n"
        "        }\n"
        "    }\n"
        "    let text = text?;\n"
        "    let mark = refs\n"
        "        .last()\n"
        "        .filter(|r| last_line && r.start_pos >= text_end)\n"
        "        .and_then(|r| metric(r.char_shape_id));\n"
        "    let (lh, bl, base) = match mark {\n"
        "        Some(m) if m.0 > text.0 => (m.0 + text.0 - text.1, m.1, m.0),\n"
        "        _ => (text.0, text.1, text.0),\n"
        "    };\n"
        "    Some((lh as i32, bl as i32, base as i32))\n"
        "}\n"
        "\n"
        "fn apply_inline_control_line_height(seg: &mut LineSeg, height_hwp: i32) {\n",
    ),
    (
        "renderer/composer/line_breaking.rs",
        "        let mut text_seg = make_line_seg(utf16_start, fs);\n",
        "        let mut text_seg = make_line_seg(utf16_start, fs);\n"
        f"        // {TAG} Word 호환 문서의 비율 간격 줄은 글꼴 세로 수치로\n"
        "        if matches!(ls_type, LineSpacingType::Percent) {\n"
        "            let last_line = lb.end_idx >= text_len;\n"
        "            let end_u16 = if last_line {\n"
        "                char_index_to_utf16_offset(para, text_len)\n"
        "            } else {\n"
        "                claude_line_start_utf16(para, lb.end_idx)\n"
        "            };\n"
        "            if let Some((lh, bl, base)) = claude_word_line_metrics(para, styles, utf16_start, end_u16, last_line, dpi) {\n"
        "                text_seg.line_height = lh;\n"
        "                text_seg.text_height = lh;\n"
        "                text_seg.baseline_distance = bl;\n"
        "                text_seg.line_spacing = compute_line_spacing_hwp(ls_type, ls_value, base, dpi);\n"
        "            }\n"
        "        }\n",
    ),
    (
        "renderer/composer/line_breaking.rs",
        "                let mut metrics = frame_metrics_for_line(\n"
        "                    maximum_font_size,\n"
        "                    fallback_font_size,\n"
        "                    line_spacing_type,\n"
        "                    line_spacing_value,\n"
        "                    dpi,\n"
        "                );\n",
        "                let mut metrics = frame_metrics_for_line(\n"
        "                    maximum_font_size,\n"
        "                    fallback_font_size,\n"
        "                    line_spacing_type,\n"
        "                    line_spacing_value,\n"
        "                    dpi,\n"
        "                );\n"
        f"                // {TAG} 본문 줄 대부분이 이 경로다(줄 배치 없는 HWPX)\n"
        "                if matches!(line_spacing_type, LineSpacingType::Percent) {\n"
        "                    let span = segments.first().zip(segments.last()).map(|(a, b)| (a.text_range.start, b.text_range.end));\n"
        "                    let (start_u16, end_u16) = span.unwrap_or((0, 0));\n"
        "                    if let Some((lh, bl, base)) =\n"
        "                        claude_word_line_metrics(para, styles, start_u16, end_u16, cursor.finished, dpi)\n"
        "                    {\n"
        "                        metrics.line_height = lh;\n"
        "                        metrics.text_height = lh;\n"
        "                        metrics.baseline_distance = bl;\n"
        "                        metrics.line_spacing = compute_line_spacing_hwp(line_spacing_type, line_spacing_value, base, dpi);\n"
        "                    }\n"
        "                }\n",
    ),
    (
        "renderer/composer/line_breaking.rs",
        "            let mut seg = make_line_seg(0, font_size);\n"
        "            if let Some(template) = orig.as_ref() {\n",
        "            let mut seg = make_line_seg(0, font_size);\n"
        f"            // {TAG} 빈 문단도 Word 호환 문서면 글꼴 세로 수치로\n"
        "            if matches!(ls_type, LineSpacingType::Percent) {\n"
        "                if let Some((lh, bl, base)) = claude_word_line_metrics(para, styles, 0, 0, true, dpi) {\n"
        "                    seg.line_height = lh;\n"
        "                    seg.text_height = lh;\n"
        "                    seg.baseline_distance = bl;\n"
        "                    seg.line_spacing = compute_line_spacing_hwp(ls_type, ls_value, base, dpi);\n"
        "                }\n"
        "            }\n"
        "            if let Some(template) = orig.as_ref() {\n",
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
