"""새 정답본 입력 d019(줄 배치 지움)의 p6(글 없는 문단에 자리 차지 표 하나, 높이 4800)에서 표를 같은 문단에 복제해,
표가 둘 이상일 때 한/글이 호스트 줄과 둘째 표, 다음 문단을 어디에 두는지 본다.

    python exp/make_multitbl.py ../out/fresh/in/d019.hwpx <출력 폴더>

변형: one(그대로), two(표 둘), three(표 셋), two_off(둘째 표 오프셋 2000), tab(표 하나 + 표 뒤 탭),
one_om, two_om(바깥 여백 283, 오프셋 375 — d322 꼴), two_om_off0(여백 283, 오프셋 0), two_off375(여백 0, 오프셋 375).
한/글 측정(hwpx_lab/measure.py) 뒤 exp/read_multitbl.py 로 엔진 SVG 와 한/글 PDF 의 표 가로선, 표 뒤 글 y 를 견준다.
"""

import copy
import sys
import zipfile
from pathlib import Path

from lxml import etree

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
PI = 6
src, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
zin = zipfile.ZipFile(src)
parts = [(i.filename, i.compress_type, zin.read(i.filename)) for i in zin.infolist()]


def variant(name, copies, off2=None, tab=False, om=None, off=None):
    with zipfile.ZipFile(out / f"m_{name}.hwpx", "w", zipfile.ZIP_DEFLATED) as z:
        for fname, ct, data in parts:
            if fname == "Contents/section0.xml":
                root = etree.fromstring(data)
                ps = [p for p in root if p.tag == f"{HP}p"]
                p = ps[PI]
                tb = p.find(f"{HP}run/{HP}tbl")
                run = tb.getparent()
                at = list(run).index(tb)
                if om is not None:
                    for side in ("left", "right", "top", "bottom"):
                        tb.find(f"{HP}outMargin").set(side, str(om))
                if off is not None:
                    tb.find(f"{HP}pos").set("vertOffset", str(off))
                for k in range(1, copies):
                    c = copy.deepcopy(tb)
                    c.set("id", str(int(tb.get("id")) + k))
                    c.set("zOrder", str(int(tb.get("zOrder")) + 100 + k))
                    if off2 is not None:
                        c.find(f"{HP}pos").set("vertOffset", str(off2))
                    run.insert(at + k, c)
                if tab:
                    t = etree.Element(f"{HP}t")
                    etree.SubElement(t, f"{HP}tab", width="4000", leader="0", type="1")
                    run.insert(at + 1, t)
                data = etree.tostring(
                    root, xml_declaration=True, encoding="UTF-8", standalone=True
                )
            z.writestr(zipfile.ZipInfo(fname), data, compress_type=ct)


variant("one", 1)
variant("two", 2)
variant("three", 3)
variant("two_off", 2, off2=2000)
variant("tab", 1, tab=True)
variant("one_om", 1, om=283, off=375)
variant("two_om", 2, om=283, off=375)
variant("two_om_off0", 2, om=283, off=0)
variant("two_off375", 2, om=0, off=375)
print("ok")
