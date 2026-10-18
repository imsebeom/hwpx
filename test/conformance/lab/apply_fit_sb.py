"""개발용: 쪽 끝 맞춤 판정에 문단 위 간격을 센다(HWPX, 저장된 줄 배치가 있는 문단).

    python apply_fit_sb.py [--revert]

정답본 모음(exp/harvest_fit_sb.py, 글 있는 문단): 위 간격 없이는 앞 쪽 바닥에 들어가는 첫 줄이 다음 쪽으로 넘어간 15건 중 14건이
「위 간격 + 첫 줄 높이」로 넘친다(남은 d010 p18 은 그 쪽에 각주가 있어 본문이 짧다 — 모음은 각주를 빼지 않았다). 같은 쪽에 남은 바닥 근처 첫 줄 40건은 모두 이 판정에 맞는다.
줄 간격(trailing)은 세지 않는다(그중 9건이 줄 + 줄 간격으로는 넘치지만 남았다). 빈 문단은 바닥을 넘어도 그 쪽에 남는다.
엔진은 줄 배치가 있으면 판정 높이를 줄 배치 폭(첫 줄 vpos ~ 끝 줄 바닥)으로 줄여 위 간격이 빠졌다(d268 p71: 854.3 + 20.0 ≤ 874.4
로 담았지만 위 간격 6.7 을 더하면 넘친다).
height_for_fit 은 저장 줄 배치 문단의 흐름 전진(flow_advance_height)에도 쓰여 그 값을 바꾸면 흐름 전체가 밀린다(첫 시도:
d159, d306 쪽수 +1). 그래서 쪽 끝 맞춤 비교(page_end_fit_height)에만 더한다. 상한은 줄 간격(trailing)을 뺀 문단 전체 높이.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx fit-sb]"

EDITS = [
    (
        "renderer/typeset.rs",
        "            omit_untrusted_empty || strict_after_empty_host_float,\n        );\n",
        "            omit_untrusted_empty || strict_after_empty_host_float,\n        );\n"
        f"        // {TAG} 한/글은 쪽 끝 맞춤에 위 간격을 센다(정답본 15/15, lab exp/harvest_fit_sb.py).\n"
        "        // height_for_fit 은 줄 배치 폭이라 위 간격이 빠져 있다 — 비교에만 더하고 흐름 전진은 그대로 둔다.\n"
        "        // 빈 문단은 쪽 바닥을 넘어도 그 쪽에 남는다(d321 p66, p124, d330 p30, p31) — 더하지 않는다.\n"
        "        let page_end_fit_height = if st.profile.hwpx_container() && st.col_count == 1 && para_has_visible_text(para) {\n"
        "            let trail = fmt.line_spacings.last().copied().unwrap_or(0.0);\n"
        "            page_end_fit_height.max(\n"
        "                (fmt.height_for_fit + fmt.spacing_before.max(0.0)).min((fmt.total_height - trail).max(0.0)),\n"
        "            )\n"
        "        } else {\n"
        "            page_end_fit_height\n"
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
