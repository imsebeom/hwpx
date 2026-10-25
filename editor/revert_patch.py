"""적용된 find/replace 패치를 소스에서 되돌린다(replace 조각을 find 조각으로). setup.mjs 의 적용 방식과 같게 나눈다.

python revert_patch.py <패치.rs> <소스 파일>

이미 적용한 patches/*.rs 를 고쳐 다시 빌드할 때 쓴다(setup.mjs 는 소스의 표식만 보고 건너뛴다). 되돌린 뒤
.build/rhwp/pkg/.claude-patched 를 지우고 setup.mjs --build. find/replace(next 조각) 꼴만 다룬다 — anchor 앞에 끼우는
꼴은 표식 줄부터 anchor 앞까지 손으로 걷는다. 2026-10-25 한 세션에서 세 번 썼다.
"""

import sys
from pathlib import Path

patch, src = Path(sys.argv[1]), Path(sys.argv[2])
text = patch.read_text(encoding="utf-8").replace("\r\n", "\n")
text = text.removeprefix("// ==== find ====\n")
blocks = [
    b.split("\n// ==== replace ====\n") for b in text.split("\n// ==== next ====\n")
]
raw = src.read_bytes().decode("utf-8")
crlf = "\r\n" in raw
s = raw.replace("\r\n", "\n")
for k, (find, replace) in reversed(list(enumerate(blocks))):
    replace = replace.removesuffix("\n")
    n = s.count(replace)
    if n != 1:
        sys.exit(f"조각 {k + 1}: replace 가 {n}번 있다")
    s = s.replace(replace, find)
src.write_bytes((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))
print("되돌림", len(blocks), "조각")
