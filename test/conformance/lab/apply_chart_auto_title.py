"""개발용: c:title 요소가 없어도 autoTitleDeleted 가 0 이고 이름 있는 계열이 하나면 그 이름을 차트 제목으로 그린다.

    python apply_chart_auto_title.py [--revert]

근거(2026-10-18 블랙박스 실측): 스킬 chart_hwpx.py 가 만든 차트(c:title 없음, autoTitleDeleted=0, 계열 「방문」 하나)를
한/글 2024 로 열어 PDF 로 뽑으니 차트 위에 「방문」 제목이 있었다. 엔진은 c:title 요소가 있을 때만 자동 제목을 그려
에디터 화면에 제목이 없었다. 계열이 여럿인데 c:title 이 없으면 종전대로 제목을 그리지 않는다(실측 없음, 엑셀과 같음).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx chart-auto-title]"

EDITS = [
    (
        "../crates/rhwp-ooxml-chart/src/renderer.rs",
        "    let effective_title: Option<String> = chart.title.clone().or_else(|| {\n"
        "        (chart.has_title_elem && !chart.auto_title_deleted).then(|| match &chart.series[..] {\n",
        f"    // {TAG} c:title 요소가 없어도 이름 있는 계열이 하나면 한/글은 그 이름을 제목으로 그린다(빌더 차트, 한/글 PDF 실측)\n"
        "    let claude_single_named = matches!(&chart.series[..], [only] if !only.name.is_empty());\n"
        "    let effective_title: Option<String> = chart.title.clone().or_else(|| {\n"
        "        ((chart.has_title_elem || claude_single_named) && !chart.auto_title_deleted).then(|| match &chart.series[..] {\n",
    ),
    (
        "../crates/rhwp-ooxml-chart/src/renderer.rs",
        "                    name: name.to_string(),\n"
        "                    values: vec![1.0, 2.0, 3.0],\n"
        "                    series_type: OoxmlChartType::Pie,\n"
        "                    ..Default::default()\n"
        "                }],\n"
        '                categories: vec!["가".into(), "나".into(), "다".into()],\n'
        "                ..Default::default()\n",
        "                    name: name.to_string(),\n"
        "                    values: vec![1.0, 2.0, 3.0],\n"
        "                    series_type: OoxmlChartType::Pie,\n"
        "                    ..Default::default()\n"
        "                }],\n"
        '                categories: vec!["가".into(), "나".into(), "다".into()],\n'
        f"                // {TAG} 이름 있는 단일 계열은 자동 제목이 붙으므로 범례 자리만 비교하게 제목을 끈다\n"
        "                auto_title_deleted: true,\n"
        "                ..Default::default()\n",
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
