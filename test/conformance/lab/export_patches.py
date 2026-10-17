"""개발용 수정 목록(apply_*.py 의 EDITS)을 editor/patches/<id>.rs 블록 패치로 내보낸다.

    python export_patches.py <apply 모듈 이름> <id 접두사>

파일마다 패치 하나(<접두사>-<파일 이름>)를 만들고, setup.mjs 의 [id, 파일] 목록에 넣을 줄을 찍는다.
각 파일의 첫 블록 바꿀 글에 [claude-hwpx …] 표지가 있어야 setup.mjs 가 이미 넣은 것을 알아본다.
"""

import importlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PATCHES = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / "patches"


def main():
    mod = importlib.import_module(sys.argv[1])
    prefix = sys.argv[2]
    by_file = {}
    for rel, find, repl, *_ in mod.EDITS:
        by_file.setdefault(rel, []).append((find, repl))
    stems = [Path(r).stem for r in by_file]
    for rel, blocks in by_file.items():
        # 표지가 든 블록을 앞으로
        blocks.sort(key=lambda b: "[claude-hwpx" not in b[1])
        if "[claude-hwpx" not in blocks[0][1]:
            sys.exit(f"{rel}: 표지가 든 블록이 없다")
        parts = []
        for find, repl in blocks:
            if find.endswith("\n") and repl.endswith("\n"):
                find, repl = find[:-1], repl[:-1]
            parts.append(f"{find}\n// ==== replace ====\n{repl}")
        # 같은 이름 파일이 둘이면(parser/hwpx/header.rs, serializer/hwpx/header.rs) 위 폴더 이름을 앞에 붙인다
        stem = Path(rel).stem
        if stems.count(stem) > 1:
            stem = f"{Path(rel).parts[0]}-{stem}"
        pid = f"{prefix}-{stem.replace('_', '-')}"
        (PATCHES / f"{pid}.rs").write_text(
            "// ==== find ====\n" + "\n// ==== next ====\n".join(parts) + "\n",
            encoding="utf-8",
        )
        print(f"    ['{pid}', 'src/{rel}'],")


if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    main()
