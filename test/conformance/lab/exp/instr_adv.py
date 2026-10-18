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
s = raw.replace("\r\n", "\n")
anchor = (
    "    fn advance_column_or_new_page(&mut self) {\n        self.flush_column();\n"
)
assert s.count(anchor) == 1
s = s.replace(
    anchor,
    "    fn advance_column_or_new_page(&mut self) {\n"
    '        if std::env::var("DBGADV").ok().and_then(|v| v.parse::<usize>().ok()) == Some(self.pages.len()) {\n'
    '            eprintln!("ADV at pages={} cur_h={:.1}\\n{}", self.pages.len(), self.current_height, std::backtrace::Backtrace::force_capture());\n'
    "        }\n"
    "        self.flush_column();\n",
)
p.write_bytes(s.replace("\n", nl).encode("utf-8"))
print("instrumented")
