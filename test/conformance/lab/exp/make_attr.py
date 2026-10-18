import os
import shutil
import zipfile

src = r"C:\Users\hccga\Desktop\code\.automation_and_skill\hwpx 에디터기반 에이전트스킬\test\conformance\out\oracle\d193.hwpx"
base = os.path.join(os.environ["TEMP"], "attr")
shutil.rmtree(base, ignore_errors=True)
os.makedirs(os.path.join(base, "in"))
os.makedirs(os.path.join(base, "rt"))
z = zipfile.ZipFile(src)
entries = [(i, z.read(i.filename)) for i in z.infolist()]
sec = next(d for i, d in entries if i.filename == "Contents/section0.xml").decode(
    "utf-8"
)
TID = "1210124188"


def edit_pos(s, repl):
    i = s.rfind("<hp:tbl ", 0, s.find("그림 4-6. 관리자"))
    j = s.find("<hp:pos ", i)
    k = s.find(">", j)
    seg = s[j:k]
    for a, b in repl:
        assert a in seg, a
        seg = seg.replace(a, b)
    return s[:j] + seg + s[k:]


def edit_tbl(s, repl):
    i = s.rfind("<hp:tbl ", 0, s.find("그림 4-6. 관리자"))
    k = s.find(">", i)
    seg = s[i:k]
    for a, b in repl:
        assert a in seg, a
        seg = seg.replace(a, b)
    return s[:i] + seg + s[k:]


variants = {
    "c_col": lambda s: edit_pos(s, [('horzRelTo="PARA"', 'horzRelTo="COLUMN"')]),
    "d_col_fwt": lambda s: edit_pos(
        s,
        [
            ('horzRelTo="PARA"', 'horzRelTo="COLUMN"'),
            ('flowWithText="0"', 'flowWithText="1"'),
        ],
    ),
    "e_cell": lambda s: edit_tbl(s, [('pageBreak="NONE"', 'pageBreak="CELL"')]),
    "f_table": lambda s: edit_tbl(s, [('pageBreak="NONE"', 'pageBreak="TABLE"')]),
}
for name, fn in variants.items():
    with zipfile.ZipFile(os.path.join(base, "in", f"{name}.hwpx"), "w") as w:
        for info, data in entries:
            if info.filename == "Contents/section0.xml":
                data = fn(sec).encode("utf-8")
            w.writestr(
                info,
                data,
                compress_type=zipfile.ZIP_STORED
                if info.filename == "mimetype"
                else zipfile.ZIP_DEFLATED,
            )
print(sorted(os.listdir(os.path.join(base, "in"))))
