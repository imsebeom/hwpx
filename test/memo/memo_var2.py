"""memo1_rt.hwpx 의 MEMO fieldBegin 속성 변형: zorder 만, metaTag 만, zorder 0"""
import re, sys, zipfile
sys.stdout.reconfigure(encoding="utf-8")
src = zipfile.ZipFile("memo1_rt.hwpx")
members = [(it, src.read(it.filename)) for it in src.infolist()]
sec = next(d for it, d in members if it.filename == "Contents/section0.xml").decode()

def variant(s, zorder, meta):
    def one(m):
        tag = m.group(0)
        num = re.search(r'name="Number">(\d+)<', s[m.end() : m.end() + 600]).group(1)
        if zorder is not None:
            tag = tag.replace(" fieldid=", f' zorder="{num if zorder == "num" else zorder}" fieldid=')
        if meta:
            tag = tag[:-1] + ' metaTag="">'
        return tag
    return re.sub(r'<hp:fieldBegin [^>]*type="MEMO"[^>]*>', one, s)

variants = {"Z": variant(sec, "num", False), "M": variant(sec, None, True), "Z0": variant(sec, "0", True), "Z9": variant(sec, "99", False)}
for name, xml in variants.items():
    out = zipfile.ZipFile(f"memo1_v{name}.hwpx", "w", zipfile.ZIP_DEFLATED)
    for it, data in members:
        if it.filename == "Contents/section0.xml":
            data = xml.encode()
        out.writestr(it, data, compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
    out.close()
    print(name, re.search(r'<hp:fieldBegin [^>]*type="MEMO"[^>]*>', xml).group(0))
