"""메모 필드 요약: 번호(zorder, Number), id, 작성자, 일시, 본문 문단. python memo_fields.py <hwpx...>"""

import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
for f in sys.argv[1:]:
    z = zipfile.ZipFile(f)
    for n in z.namelist():
        if not re.match(r"Contents/section\d+\.xml", n):
            continue
        s = z.read(n).decode()
        ends = re.findall(r'<hp:fieldEnd\b[^>]*beginIDRef="([^"]*)"', s)
        print("==", f, n, "memogroup", s.count("<hp:memogroup"), "fieldEnd", len(ends))
        for m in re.finditer(r'<hp:fieldBegin\b([^>]*type="MEMO"[^>]*)>', s):
            a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
            tail = s[m.end() : s.find("</hp:fieldBegin>", m.end())]
            p = dict(re.findall(r'name="(\w+)"\s*>([^<]*)<', tail))
            paras = re.findall(r"<hp:p\b([^>]*)>(.*?)</hp:p>", tail, re.S)
            body = [
                (
                    "".join(re.findall(r"<hp:t\b[^>]*>([^<]*)</hp:t>", x)),
                    dict(re.findall(r'(\w+)="([^"]*)"', at)),
                )
                for at, x in paras
            ]
            print(
                f"  id={a.get('id')} zorder={a.get('zorder')} Number={p.get('Number')} ID={p.get('ID')} 작성자={p.get('Author')!r} "
                f"일시={p.get('CreateDateTime')} 끝표식={'있음' if a.get('id') in ends else '없음'} Command={p.get('Command')}"
            )
            for text, at in body:
                print(
                    f"      문단(style {at.get('styleIDRef')}, paraPr {at.get('paraPrIDRef')}): {text[:40]}"
                )
