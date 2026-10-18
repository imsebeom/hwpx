"""개발용: 글 없는 문단의 자리 차지 표(문단 기준, 글자처럼 취급 아님) 바로 뒤 본문 문단은 위 간격을 표 아래에 묻는다(HWPX).

    python apply_tbl_next_sb.py [--revert]

정답본 모음(exp/harvest_tbl_nextsb.py): 글이 표보다 짧은 호스트 뒤 문단의 첫 줄 vpos 는 표 바닥과 같다(빈 호스트 16, 글 있는 호스트 3,
모두 「묻음」, 「더함」 0). 엔진은 표를 놓으며 흐름을 표 바닥까지 내린 뒤 다음 문단 위 간격을 또 더했다. d268 둘째 구역 p244(빈 문단,
표 높이 54467, 오프셋 1551, 바깥 여백 140x2) 뒤 p245(위 간격 700): 한/글 새 조판은 첫 줄을 60287(= 표 바닥)에 두는데 엔진은 700 아래.
쪽 끝 빈 문단 p254 가 다음 쪽으로 밀려 마지막 표(p258)까지 한 쪽 늘었다.
float-sb-absorb(밀어낸 문단만)는 이 경로(표를 놓으며 흐름에 이미 넣음)를 잡지 못한다. 빈 호스트만 다룬다.
조판(쪽 나눔)만 바꾼다. 그리기 위치는 layout 이 따로 정한다(d268 21쪽 p245 는 전후 모두 729.6pt, 한/글 711.5pt — 따로 볼 것).
새 정답본(out/fresh) 쪽수 99.4 → 99.7%(d268 24 → 23쪽), 옛 정답본 99.1 → 99.4%, 줄바꿈과 문단 쪽 그대로.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx tbl-next-sb]"

FIND = (
    "                self.typeset_paragraph(\n"
    "                    &mut st,\n"
    "                    para_idx,\n"
    "                    para,\n"
    "                    &formatted,\n"
)

EDITS = [
    (
        "renderer/typeset.rs",
        FIND,
        f"                // {TAG} 글 없는 문단의 자리 차지 표 바로 뒤 문단은 위 간격을 표 아래에 묻는다(정답본 19/19, lab exp/harvest_tbl_nextsb.py)\n"
        "                if st.profile.hwpx_container()\n"
        "                    && formatted.spacing_before > 0.0\n"
        "                    && para_idx > 0\n"
        "                    && matches!(st.current_items.last(), Some(PageItem::Table { para_index, .. }) if *para_index + 1 == para_idx)\n"
        "                    && paragraphs.get(para_idx - 1).is_some_and(|host| {\n"
        "                        !para_has_non_whitespace_text(host)\n"
        "                            && host.controls.iter().filter(|c| matches!(c, Control::Table(_))).count() == 1\n"
        "                            && host.controls.iter().any(|c| matches!(c, Control::Table(t)\n"
        "                                if crate::renderer::float_placement::is_para_topbottom_float(&t.common)))\n"
        "                    })\n"
        "                {\n"
        "                    st.current_height = (st.current_height - formatted.spacing_before).max(0.0);\n"
        "                }\n" + FIND,
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
