import shutil
import sys
from pathlib import Path

p = (
    Path.home()
    / ".claude/skills/hwpx/editor/.build/rhwp/src/renderer/layout/table_layout.rs"
)
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
    "        for (i, cell) in row_cells.iter().enumerate() {\n"
    "            let units = self.cell_units(cell, table, styles);\n"
    "            let start = start_cut.get(i).copied().unwrap_or(0).min(units.len());\n"
    "            let mut j = start;\n"
)
assert s.count(anchor) == 1, s.count(anchor)
s = s.replace(
    anchor,
    anchor
    + '            if std::env::var("DBGUNITS").is_ok() { eprintln!("UNITS row={} avail={:.1} {:?}", row, avail_height, units.iter().map(|u| (format!("{:.1}", u.height), u.stored_frame_break_before, u.hard_break_before, u.empty_spacer, u.para_idx)).collect::<Vec<_>>()); }\n',
)
p.write_bytes(s.replace("\n", nl).encode("utf-8"))
print("instrumented")
