"""개발용: 줄을 빈칸 묶음(2개 이상) 가운데서 꺾을 때 앞줄에 빈칸을 적어도 둘 남긴다.

    python apply_space_run_keep2.py [--revert]

근거(2026-10-18 블랙박스 실측):
- e35: 「가」 43자 + 빈칸 2, 3, 5개 + 「나다라마」, 양쪽 정렬. 오른쪽 여백 300~700(남는 폭이 빈칸 하나보다 좁음)에서
  한/글은 빈칸 둘을 앞줄에 남겼고 rhwp 는 하나였다. 여백 0~200(넓음)은 둘 다 2, 여백 800 이상은 어절이 안 들어가 둘 다 앞에서 꺾음.
- 정답본 전체(harvest_spacerun.py): 빈칸 묶음 가운데서 꺾인 자리 약 150곳 중 한/글이 하나만 남긴 곳 0, 폭이 남으면 3~10.
  불일치 40곳 가까이(d007, d132, d263 …)가 이 자리였다.
space-no-overflow(e19)의 「시작 위치가 줄 폭 안인 빈칸은 남긴다」는 그대로 두고, 그 결과가 하나면 둘로 올린다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx space-run-keep2]"

EDITS = [
    (
        "renderer/composer/line_breaking.rs",
        "    let mut w = before;\n"
        "    for (idx, sw) in spaces {\n"
        "        if w > effective_width {\n"
        "            return Some(idx);\n"
        "        }\n",
        "    let mut w = before;\n"
        "    for (idx, sw) in spaces {\n"
        "        if w > effective_width {\n"
        f"            // {TAG} 빈칸 묶음 가운데서 꺾으면 남는 폭이 빈칸 하나보다 좁아도 앞줄에 빈칸을 적어도 둘 남긴다(e35, 정답본 약 150곳)\n"
        "            let keep2 = run_start + 2;\n"
        "            return if keep2 >= run_end { None } else { Some(idx.max(keep2)) };\n"
        "        }\n",
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
