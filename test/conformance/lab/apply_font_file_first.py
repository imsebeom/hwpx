"""개발용: 실행 중 등록한 글꼴 파일 폭 표를 내장 표보다 먼저 보게 한다(확인 뒤 editor/patches 로 옮긴다).

    python apply_font_file_first.py [--revert]

근거(lab e2, e5): 굴림, 바탕, 돋움, 나눔고딕, 맑은 고딕, 한컴산뜻돋움은 한/글 2024 PDF 글자 폭이 설치된 글꼴 파일의
전진 폭과 0.01em 안에서 같은데, 내장 표는 `…`, `▪`, `◦`, `■` 같은 기호에서 크게 달랐다. 어느 글꼴을 파일로 읽을지는
에디터(font-metrics.mjs)가 정한다(함초롬 계열은 한/글 값이 파일과 달라 빼고 내장 표를 쓴다).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx font-file-first]"

EDITS = [
    (
        "renderer/font_metrics_data.rs",
        "    let Some(slots) = metric_index().get(alias_resolved_name) else {\n"
        "        return claude_runtime_metric_decision(name, alias_resolved_name, alias_rule_id, bold);\n"
        "    };\n",
        f"    // {TAG} 실행 중에 등록한 표(설치된 글꼴 파일)가 있으면 내장 표보다 먼저 쓴다. 한/글 2024 는 글꼴 파일의\n"
        "    // 전진 폭으로 조판한다(test/conformance/lab e2, e5). 무엇을 등록할지는 에디터 font-metrics.mjs 가 정한다.\n"
        "    if let Some(decision) = claude_runtime_metric_decision(name, alias_resolved_name, alias_rule_id, bold) {\n"
        "        return Some(decision);\n"
        "    }\n"
        "    let Some(slots) = metric_index().get(alias_resolved_name) else {\n"
        "        return None;\n"
        "    };\n",
    ),
    (
        "renderer/font_metrics_data.rs",
        "        if name.is_empty() || em == 0 || em > u64::from(u16::MAX) || claude_has_builtin_metric(name)\n"
        "        {\n",
        "        // 내장 표가 있는 글꼴도 받는다(위 font-file-first). 무엇을 보낼지는 에디터가 정한다\n"
        "        if name.is_empty() || em == 0 || em > u64::from(u16::MAX) {\n",
    ),
]


def main():
    revert = "--revert" in sys.argv
    for rel, find, repl in EDITS:
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
