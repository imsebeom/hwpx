"""개발용: cut-row-pad(내용이 선언 높이를 넘는 칸은 줄이지 않은 여백으로 행을 키운다)를 저장 줄 기록이 있는 HWPX 칸에도 쓴다.

    python apply_cut_row_pad_stored.py [--revert]

근거(2026-10-18 issue1949 표본, 한/글 PDF): 표 머리 두 행(선언 282 = 여백 141 + 141, 글 1200)의 줄 간격이 한/글 PDF 에서
19.81px(1486 HU)로 원래 여백을 쓴 1482 와 맞는다. 엔진은 저장 줄 기록이 있는 칸을 이 판정에서 빼 여백을 절반으로 줄여(1341)
1쪽 행 예산이 282 HU 후했고, 편집으로 저장 쪽 경계가 풀리면 한/글이 37줄을 두는 자리에 38줄을 담았다(make_edit1949.py).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx cut-row-pad-stored]"

EDITS = [
    (
        "renderer/layout/table_layout.rs",
        "                if content > decl_h\n"
        "                    && cell\n"
        "                        .paragraphs\n"
        "                        .iter()\n"
        "                        .all(crate::renderer::para_has_no_stored_line_segs)\n",
        "                if content > decl_h\n"
        f"                    // {TAG} HWPX 는 저장 줄 기록이 있어도 같다(issue1949 머리 행: 한/글 PDF 행 간격 1486 HU = 1200 + 141 + 141)\n"
        "                    && (self.profile.get().hwpx_container()\n"
        "                        || cell\n"
        "                            .paragraphs\n"
        "                            .iter()\n"
        "                            .all(crate::renderer::para_has_no_stored_line_segs))\n",
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
