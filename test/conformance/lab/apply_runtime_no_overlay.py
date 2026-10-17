"""개발용: 실행 중 등록한 폭 표(설치된 글꼴 파일, 한/글 실측 표)에서 온 폭은 문장 부호 덮어쓰기와 ㆍ 대체를 하지 않는다.

    python apply_runtime_no_overlay.py [--revert]

근거(lab e20, 글꼴 12종 40pt): 한/글 2024 는 글꼴 파일에 있는 글자를 파일 폭 그대로 쓴다. HY헤드라인M, HY울릉도M, 바탕체,
굴림체의 전각 `·` ‘ ’ “ ” `…`(파일 1em)도 1em, 모든 글꼴의 ㆍ(파일 1em)도 1em 이다. 엔진은 1em 이상인 문장 부호를
0.3em(‘ ’ ·)이나 0.5em(“ ” …)으로, ㆍ를 0.5em 으로 눌렀다. 이 덮어쓰기는 내장 표 경로에는 그대로 둔다(HWP5 문서 등).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx runtime-no-overlay]"
REL = "renderer/layout/text_measurement.rs"

EDITS = [
    (
        REL,
        "        let is_halfwidth_punct = matches!(c, '\\u{2018}'..='\\u{2027}');\n",
        f"        // {TAG} 실행 중 등록한 표(entry_index = usize::MAX: 글꼴 파일, 한/글 실측)의 폭은 한/글 2024 가 그대로 쓴다(lab e20)\n"
        "        let runtime_metric = mm.entry_index == usize::MAX;\n"
        "        let is_halfwidth_punct = !runtime_metric && matches!(c, '\\u{2018}'..='\\u{2027}');\n",
    ),
    (
        REL,
        "        let is_narrow_unicode_punct = matches!(c, '\\u{2018}' | '\\u{2019}' | '\\u{2027}');\n"
        "        let is_b7_notdef_artifact =\n"
        "            c == '\\u{00B7}' && glyph_w >= mm.metric.em_size && !is_monospace_metric(mm.metric);\n",
        "        let is_narrow_unicode_punct =\n"
        "            !runtime_metric && matches!(c, '\\u{2018}' | '\\u{2019}' | '\\u{2027}');\n"
        "        let is_b7_notdef_artifact = !runtime_metric\n"
        "            && c == '\\u{00B7}'\n"
        "            && glyph_w >= mm.metric.em_size\n"
        "            && !is_monospace_metric(mm.metric);\n",
    ),
    (
        REL,
        "pub(crate) fn area_dot_fallback_width(font_family: &str, font_size: f64) -> Option<f64> {\n"
        "    let fam = font_family.split(',').next().unwrap_or(\"\").trim();\n",
        "pub(crate) fn area_dot_fallback_width(font_family: &str, font_size: f64) -> Option<f64> {\n"
        "    let fam = font_family.split(',').next().unwrap_or(\"\").trim();\n"
        "    // [claude-hwpx runtime-no-overlay] 실행 중 등록한 표에 ㆍ 가 있으면 그 폭을 쓴다(한/글 2024 는 파일 폭, 글꼴 12종 모두 1em)\n"
        "    if font_metrics_data::find_metric_decision(fam.trim_matches('\\'').trim_matches('\"'), false, false)\n"
        "        .is_some_and(|mm| mm.entry_index == usize::MAX && mm.metric.get_width('\\u{318D}').is_some())\n"
        "    {\n"
        "        return None;\n"
        "    }\n",
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
