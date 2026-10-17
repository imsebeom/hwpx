"""개발용: rhwp 소스에 useFontSpace 규칙을 직접 넣는다(확인 뒤 editor/patches 로 옮긴다)."""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[3] / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx use-font-space]"

EDITS = [
    (
        "renderer/mod.rs",
        "    pub kerning: bool,\n    /// 자간 (px)\n",
        "    pub kerning: bool,\n"
        f"    /// {TAG} 글자 모양의 「글꼴에 어울리는 빈칸」. 켜지면 빈칸은 글꼴 고유 폭이고, 꺼지면 한/글은 글자 크기의\n"
        "    /// 절반을 쓴다(한/글 2024 실측: 글꼴 5종 × 장평과 자간 2종, PDF 글자 위치).\n"
        '    #[serde(skip_serializing_if = "std::ops::Not::not")]\n'
        "    pub use_font_space: bool,\n"
        "    /// 자간 (px)\n",
    ),
    (
        "renderer/mod.rs",
        "            kerning: false,\n            letter_spacing: 0.0,\n",
        "            kerning: false,\n            use_font_space: false,\n            letter_spacing: 0.0,\n",
    ),
    (
        "renderer/style_resolver.rs",
        "    pub kerning: bool,\n    /// 음영 색",
        f"    pub kerning: bool,\n    /// {TAG} 글꼴에 어울리는 빈칸\n    pub use_font_space: bool,\n    /// 음영 색",
    ),
    (
        "renderer/style_resolver.rs",
        "            kerning: false,\n            shade_color: 0x00FFFFFF,\n",
        "            kerning: false,\n            use_font_space: false,\n            shade_color: 0x00FFFFFF,\n",
    ),
    (
        "renderer/style_resolver.rs",
        "        kerning: cs.kerning,\n        shade_color: cs.shade_color,\n",
        "        kerning: cs.kerning,\n        use_font_space: cs.use_font_space,\n        shade_color: cs.shade_color,\n",
    ),
    (
        "renderer/layout/text_measurement.rs",
        "            kerning: cs.kerning,\n            // 단일 출처",
        "            kerning: cs.kerning,\n            use_font_space: cs.use_font_space,\n            // 단일 출처",
    ),
    (
        "renderer/layout/text_measurement.rs",
        "pub(crate) fn hancom_regenerated_space_width(style: &TextStyle) -> Option<f64> {\n",
        "pub(crate) fn hancom_regenerated_space_width(style: &TextStyle) -> Option<f64> {\n"
        f"    // {TAG} 반각 공백은 「글꼴에 어울리는 빈칸」이 꺼진 글자 모양의 규칙이다. 켜져 있으면 글꼴 고유 폭 그대로.\n"
        "    if style.use_font_space {\n        return None;\n    }\n",
    ),
    (
        "renderer/composer.rs",
        "fn regenerated_half_space_width(style: &TextStyle) -> f64 {\n",
        "fn regenerated_half_space_width(style: &TextStyle) -> f64 {\n"
        f"    // {TAG} 「글꼴에 어울리는 빈칸」이 켜진 글자 모양은 반각 칸이 아니라 글꼴 고유 폭이다.\n"
        "    if style.use_font_space {\n"
        '        return estimate_text_width_unrounded(" ", style);\n'
        "    }\n",
    ),
    (
        "renderer/layout/text_measurement.rs",
        "    let dash_leader = is_dash_leader_run(chars, i);\n",
        "    // [claude-hwpx use-font-space-own] 폭 표는 빈칸을 반각(또는 한컴 PDF 실측값)으로 바꿔 돌려준다. 이는 「글꼴에\n"
        "    // 어울리는 빈칸」이 꺼진 글자 모양의 규칙이고, 켜져 있으면 한/글은 글꼴 파일의 빈칸 폭을 쓴다(한/글 2024 실측:\n"
        "    // 맑은 고딕 720/2048, 함초롬바탕 300/1000, 굴림 341/1024 em 이 PDF 글자 위치와 맞음 — test/conformance/lab e1).\n"
        "    let (base_width_raw, width_source) = match (c, style.use_font_space, width_source, metric) {\n"
        '        (\' \', true, "metricHalfSpace" | "metricSpaceOverlay", Some(lookup)) => lookup\n'
        "            .metric\n"
        "            .get_width(' ')\n"
        '            .map(|w| (f64::from(w) * font_size / f64::from(lookup.metric.em_size), "metricFontSpace"))\n'
        "            .unwrap_or((base_width_raw, width_source)),\n"
        "        _ => (base_width_raw, width_source),\n"
        "    };\n"
        "    let dash_leader = is_dash_leader_run(chars, i);\n",
    ),
]


def main():
    # --revert: 넣은 것을 되돌린다(회귀 비교용 「패치 전」 엔진을 만들 때)
    revert = "--revert" in sys.argv
    for rel, find, repl in EDITS:
        if revert:
            find, repl = repl, find
        f = SRC / rel
        raw = f.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        s = raw.replace("\r\n", "\n")
        # 되돌릴 때는 원래 글이 고친 글 안에 들어 있을 수 있어 「고친 글이 없음」으로만 판정한다
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
