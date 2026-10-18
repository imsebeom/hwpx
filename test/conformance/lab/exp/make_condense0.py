"""d268 사본에서 둘째 구역 p121 의 문단 모양(id 56, condense=0, 양쪽 정렬)의 오른쪽 여백을 바꿔 첫 줄 폭을 줄여 간다.
한/글이 빈칸을 얼마나 줄여서라도 한 줄에 담는지 본다(read_condense0.py).

    python exp/make_condense0.py ../out/oracle/d268.hwpx <출력 폴더>

변형: 오른쪽 여백 r = 0~3000(100 간격) x condense 0, 20. 줄 배치는 지운다.
p121 첫 줄(빈칸 9개, 빈칸 폭 합 약 6252)의 자연 폭은 약 48280 으로 줄 폭 48188 을 92 넘는데 한/글은 한 줄에 담는다.
"""

import re
import sys
import zipfile
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
zin = zipfile.ZipFile(src)
parts = [(i.filename, i.compress_type, zin.read(i.filename)) for i in zin.infolist()]
SEG = re.compile(r"<hp:linesegarray>.*?</hp:linesegarray>", re.S)
n = 0
for cond in (0, 20):
    for r in range(0, 3001, 100):
        with zipfile.ZipFile(
            out / f"m_c{cond}_r{r:04d}.hwpx", "w", zipfile.ZIP_DEFLATED
        ) as z:
            for fname, ct, data in parts:
                if re.match(r"Contents/section\d+\.xml", fname):
                    data = SEG.sub("", data.decode("utf-8")).encode("utf-8")
                elif fname == "Contents/header.xml":
                    s = data.decode("utf-8")
                    m = re.search(r'<hh:paraPr id="56"[\s\S]*?</hh:paraPr>', s)
                    pp = m.group(0).replace('condense="0"', f'condense="{cond}"')
                    case, default = pp.split("<hp:default>")
                    case = case.replace('<hc:right value="0"', f'<hc:right value="{r}"')
                    default = default.replace(
                        '<hc:right value="0"', f'<hc:right value="{2 * r}"'
                    )
                    s = s[: m.start()] + case + "<hp:default>" + default + s[m.end() :]
                    data = s.encode("utf-8")
                z.writestr(zipfile.ZipInfo(fname), data, compress_type=ct)
        n += 1
print("ok", n)
