"""개발용: 대체 글꼴로 바뀌는 한컴 글꼴(HCI Poppy → Palatino Linotype 등)에 한/글에서 잰 폭 표가 등록돼 있으면
폭은 원래 글꼴 이름의 표로 재고, 그리기는 대체 글꼴로 한다(확인 뒤 editor/patches 로 옮긴다).

    python apply_hft_source_name.py [--revert]

근거(lab e9): 한/글 2024 의 HCI Poppy 폭은 대체 글꼴 Palatino Linotype 파일과 거의 같지만 `·` 385/250,
`'` 277/208, `/` 606/320 이 다르다. 대체 이름으로만 폭을 재서 d110 등에서 늦게 끊었다.
글꼴 이름 목록을 「원래 이름,대체 이름」으로 두면 폭 측정은 첫 이름(등록 표)을 쓰고, 그리기는 브라우저에 없는
첫 이름을 건너뛰어 대체 글꼴로 한다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx hft-source-name]"

EDITS = [
    (
        "renderer/font_metrics_data.rs",
        "fn claude_runtime_metric_decision<'a>(\n",
        f"/// {TAG} 이 이름으로 실행 중에 등록한 폭 표가 있는가(대체 글꼴 대신 원래 이름으로 잴지 고를 때 묻는다).\n"
        "pub(crate) fn claude_runtime_has_metric(name: &str) -> bool {\n"
        "    if !CLAUDE_RUNTIME_ANY.load(std::sync::atomic::Ordering::Relaxed) {\n"
        "        return false;\n"
        "    }\n"
        "    CLAUDE_RUNTIME_METRICS\n"
        "        .get()\n"
        "        .and_then(|lock| lock.read().ok())\n"
        "        .is_some_and(|map| map.contains_key(name))\n"
        "}\n"
        "\n"
        "fn claude_runtime_metric_decision<'a>(\n",
    ),
    (
        "renderer/style_resolver.rs",
        "            decision.css_family_chain.push(resolved.clone());\n",
        f"            // {TAG} 대체되는 글꼴이라도 원래 이름으로 폭 표(한/글 실측)가 등록돼 있으면 원래 이름을 앞에 둔다.\n"
        "            // 폭은 첫 이름으로 재고, 그리기는 브라우저에 없는 원래 이름을 건너뛰어 대체 글꼴로 한다.\n"
        "            if substitution.is_some()\n"
        "                && resolved != *name\n"
        "                && crate::renderer::font_metrics_data::claude_runtime_has_metric(name)\n"
        "            {\n"
        "                decision.css_family_chain.push(name.clone());\n"
        "            }\n"
        "            decision.css_family_chain.push(resolved.clone());\n",
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
