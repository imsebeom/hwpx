"""memo1_rt.hwpx 의 메모 필드를 조금씩 바꾼 변형을 만든다: python memo_var.py"""

import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
src = zipfile.ZipFile("memo1_rt.hwpx")
members = [(it, src.read(it.filename)) for it in src.infolist()]
sec = next(d for it, d in members if it.filename == "Contents/section0.xml").decode()


def with_zorder(s):
    def one(m):
        tag = m.group(0)
        num = re.search(r'name="Number">(\d+)<', s[m.end() : m.end() + 600])
        return (
            tag.replace(
                " fieldid=", f' zorder="{num.group(1) if num else 0}" fieldid='
            ).replace(">", ' metaTag="">', 1)
            if tag.endswith(">")
            else tag
        )

    return re.sub(r'<hp:fieldBegin [^>]*type="MEMO"[^>]*>', one, s)


def body_id0(s):
    def one(m):
        return re.sub(r'(<hp:subList[^>]*><hp:p id=")\d+', r"\g<1>0", m.group(0))

    return re.sub(
        r'<hp:fieldBegin [^>]*type="MEMO".*?</hp:fieldBegin>', one, s, flags=re.S
    )


def empty_t(s):
    return re.sub(r"(<hp:fieldEnd [^>]*/></hp:ctrl>)(</hp:run>)", r"\1<hp:t/>\2", s)


variants = {
    "A": with_zorder(sec),
    "B": body_id0(sec),
    "C": empty_t(sec),
    "ABC": empty_t(body_id0(with_zorder(sec))),
}
for name, xml in variants.items():
    out = zipfile.ZipFile(f"memo1_v{name}.hwpx", "w", zipfile.ZIP_DEFLATED)
    for it, data in members:
        if it.filename == "Contents/section0.xml":
            data = xml.encode()
        out.writestr(
            it,
            data,
            compress_type=zipfile.ZIP_STORED
            if it.filename == "mimetype"
            else zipfile.ZIP_DEFLATED,
        )
    out.close()
    print(name, "changed" if xml != sec else "same", len(xml))
