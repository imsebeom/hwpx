"""g_fix.hwpx 의 메모 Command 작성자 칸을 여러 표기로 바꾼 변형을 만든다(한/글이 어떻게 읽는지 보려고)."""

import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
BS = chr(92)  # 역슬래시
src = zipfile.ZipFile("g_fix.hwpx")
members = [(it, src.read(it.filename)) for it in src.infolist()]
sec = next(d for it, d in members if it.filename == "Contents/section0.xml").decode()
# 메모 번호 → Command 작성자 칸에 넣을 글
variants = {
    1: f"A{BS}/B{BS};C",  # 빗금과 쌍반점을 역슬래시로 이스케이프
    2: "A/B;C",  # 그대로
    3: f"A{BS}:B{BS}{BS}C",  # 쌍점과 역슬래시 이스케이프
    4: "A:B,C D",  # 쌍점, 쉼표, 공백 그대로
}
tail = "/" + BS + ";;</hp:stringParam>"
for n, author in variants.items():
    head = f'<hp:stringParam name="Command">MEMO/65535/{n}/'
    i = sec.index(head)
    j = sec.index(tail, i)
    parts = sec[i + len(head) : j].split("/")  # 하위, 상위, 작성자
    assert len(parts) == 3, parts
    sec = (
        sec[: i + len(head)]
        + "/".join(parts[:2] + [author.replace("&", "&amp;")])
        + sec[j:]
    )
out = zipfile.ZipFile("g_cmd.hwpx", "w", zipfile.ZIP_DEFLATED)
for it, data in members:
    if it.filename == "Contents/section0.xml":
        data = sec.encode()
    out.writestr(
        it,
        data,
        compress_type=zipfile.ZIP_STORED
        if it.filename == "mimetype"
        else zipfile.ZIP_DEFLATED,
    )
out.close()
for m in re.finditer(r'name="Command">([^<]*)<', sec):
    print(m.group(1))
