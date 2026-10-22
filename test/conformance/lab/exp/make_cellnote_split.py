"""쪽에 걸친 표 칸 안 각주를 한/글이 어느 쪽에 두는지 가리는 변형을 만든다(가이드북 파트2 합본의 「API」 상자 표).

    python make_cellnote_split.py <파트2 합본 hwpx> <출력 폴더>

본문 = 구역 첫 문단 + 채움 문단 K개 + 상자 표(칸 = 각주 든 제목 문단 + 일반 문단 N개, tail 이면 제목 문단을 맨 뒤로) + 뒤 문단 3개.
한/글로 열어 PDF 를 만든 뒤(REA hwpx_lab/measure.py) 각주 글과 표지가 몇 쪽에 있는지 read_cellnote_split.py 로 본다.
"""

import os
import re
import shutil
import sys
import zipfile

src, base = sys.argv[1], sys.argv[2]
shutil.rmtree(base, ignore_errors=True)
os.makedirs(os.path.join(base, "in"))
os.makedirs(os.path.join(base, "rt"))
z = zipfile.ZipFile(src)
entries = [(i, z.read(i.filename)) for i in z.infolist()]
sec = next(d for i, d in entries if i.filename == "Contents/section0.xml").decode(
    "utf-8"
)


def span(s, start, open_re, close_tag):
    """start 의 여는 태그와 짝인 닫는 태그 끝까지. 스스로 닫는 태그(<hp:p .../>)는 세지 않는다."""
    d = 0
    for m in re.finditer(f"{open_re}[^>]*>|{re.escape(close_tag)}", s[start:]):
        if m.group(0) == close_tag:
            d -= 1
        elif m.group(0).endswith("/>"):
            if d == 0:
                return start + m.end()
            continue
        else:
            d += 1
        if d == 0:
            return start + m.end()
    raise ValueError(close_tag)


def para_at(s, pos):
    """pos 를 품은 가장 바깥이 아닌(가장 가까운) 문단."""
    p = s.rfind("<hp:p ", 0, pos)
    return p, span(s, p, r"<hp:p ", "</hp:p>")


body_start = sec.find("<hp:p ")
first_p_end = span(sec, body_start, r"<hp:p ", "</hp:p>")
head, first_p = sec[:body_start], sec[body_start:first_p_end]
mark = sec.find("API — 다양한 서비스와</hp:t><hp:ctrl><hp:footNote")


def paras_in(s, a, b):
    """a~b 사이 같은 깊이 문단들의 (시작, 끝)."""
    out = []
    p = s.find("<hp:p ", a)
    while 0 <= p < b:
        e = span(s, p, r"<hp:p ", "</hp:p>")
        out.append((p, e))
        p = s.find("<hp:p ", e)
    return out


def containing(spans, pos):
    return next((a, b) for a, b in spans if a <= pos < b)


host, host_end = containing(paras_in(sec, body_start, len(sec)), mark)
tbl = sec.find("<hp:tbl ", host)
sl = sec.find("<hp:subList", tbl)
sl_open_end = sec.find(">", sl) + 1
sl_end = span(sec, sl, r"<hp:subList", "</hp:subList>")
sl_close = sl_end - len("</hp:subList>")
cell_paras = paras_in(sec, sl_open_end, sl_close)
title = sec[slice(*containing(cell_paras, mark))]
plain = sec[slice(*containing(cell_paras, sec.find("9장에서는 내 앱이", tbl)))]
filler_pos = sec.find("아래 표는 이 책에서 소개한 도구와")
fl_s, fl_e = para_at(sec, filler_pos)
filler = sec[fl_s:fl_e]
tail_xml = sec[sec.rfind("</hs:sec>") :]


def variant(k, n, tail=False):
    cell = [plain] * n
    cell = cell + [title] if tail else [title] + cell
    t = sec[host:sl_open_end] + "".join(cell) + sec[sl_close:host_end]
    body = first_p + filler * k + t + filler * 3
    return head + body + tail_xml


CASES = {
    "k10_n30": (10, 30, False),
    "k10_n50": (10, 50, False),
    "k10_n60": (10, 60, False),
    "k10_n80": (10, 80, False),
    "k10_n60_tail": (10, 60, True),
    "k10_n80_tail": (10, 80, True),
}
for i in range(66, 80, 2):
    CASES[f"k10_n{i}"] = (10, i, False)
for name, (k, n, tail) in CASES.items():
    out = os.path.join(base, "in", name + ".hwpx")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as w:
        for info, data in entries:
            if info.filename == "Contents/section0.xml":
                data = variant(k, n, tail).encode("utf-8")
            w.writestr(info, data)
    print(name)
