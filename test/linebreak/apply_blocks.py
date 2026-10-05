"""setup.mjs 의 묶음 패치 적용과 같은 규칙으로 패치 파일 하나를 소스에 넣는다: python apply_blocks.py <소스> <패치>"""
import sys
src_path, patch_path = sys.argv[1], sys.argv[2]
src = open(src_path, encoding="utf-8", newline="").read()
patch = open(patch_path, encoding="utf-8").read().replace("\r\n", "\n")
assert patch.startswith("// ==== find ====\n")
blocks = [b.split("\n// ==== replace ====\n") for b in patch[len("// ==== find ====\n"):].split("\n// ==== next ====\n")]
crlf = "\r\n" in src
eol = (lambda s: s.replace("\n", "\r\n")) if crlf else (lambda s: s)
for i, (find, replace) in enumerate(blocks):
    replace = replace[:-1] if replace.endswith("\n") else replace
    n = len(src.split(eol(find))) - 1
    assert n == 1, f"조각 {i + 1}: {n}곳"
    src = src.replace(eol(find), eol(replace))
open(src_path, "w", encoding="utf-8", newline="").write(src)
print("applied", len(blocks), src_path.replace("\\", "/").rsplit("/", 1)[-1])
