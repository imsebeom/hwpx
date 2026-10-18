import re
import shutil
import sys
from pathlib import Path

p = Path.home() / ".claude/skills/hwpx/editor/.build/rhwp/src/renderer/typeset.rs"
bak = Path(sys.argv[1])
if sys.argv[2:] == ["restore"]:
    shutil.copyfile(bak, p)
    print("restored")
    sys.exit()
shutil.copyfile(p, bak)
raw = p.read_bytes().decode("utf-8")
nl = "\r\n" if "\r\n" in raw else "\n"
lines = raw.split(nl)
out = []
n = 0
for i, line in enumerate(lines, 1):
    if re.match(r"^\s+st\.current_height (=|\+=|-=) ", line) and line.rstrip().endswith(
        ";"
    ):
        ind = line[: len(line) - len(line.lstrip())]
        out.append(line)
        out.append(
            f'{ind}if std::env::var("DBGCH").is_ok() {{ eprintln!("CH L{i} -> {{:.1}}", st.current_height); }}'
        )
        n += 1
    else:
        out.append(line)
p.write_bytes(nl.join(out).encode("utf-8"))
print("instrumented", n)
