import os
import shutil
import zipfile

src = r"C:\Users\hccga\Desktop\code\.automation_and_skill\hwpx 에디터기반 에이전트스킬\test\conformance\out\oracle\d193.hwpx"
out = os.path.join(os.environ["TEMP"], "fwt", "in")
shutil.rmtree(out, ignore_errors=True)
os.makedirs(out)
z = zipfile.ZipFile(src)
entries = []
for i in z.infolist():
    try:
        data = z.read(i.filename)
    except zipfile.BadZipFile:
        raise
    entries.append((i, data))
print("read", len(entries))
TID = "1210124188"


def set_fwt(s, v):
    i = s.find(f'<hp:tbl id="{TID}"')
    j = s.find("<hp:pos ", i)
    k = s.find(">", j)
    seg = s[j:k]
    assert 'flowWithText="0"' in seg
    return s[:j] + seg.replace('flowWithText="0"', f'flowWithText="{v}"') + s[k:]


def write(name, fn):
    with zipfile.ZipFile(os.path.join(out, name), "w") as w:
        for info, data in entries:
            if info.filename == "Contents/section0.xml":
                data = fn(data.decode("utf-8")).encode("utf-8")
            w.writestr(
                info,
                data,
                compress_type=zipfile.ZIP_STORED
                if info.filename == "mimetype"
                else zipfile.ZIP_DEFLATED,
            )


write("a_orig.hwpx", lambda s: s)
write("b_fwt1.hwpx", lambda s: set_fwt(s, 1))
print(os.listdir(out))
