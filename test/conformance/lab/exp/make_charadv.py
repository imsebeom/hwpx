"""d268 사본의 둘째 구역 p121(휴먼명조 14pt, 앞 run 자간 0, 뒤 run 자간 -2%)에 글자 하나를 16번씩 넣은 변형을 만든다.
한/글 PDF 와 엔진에서 글자 전진 폭을 16글자 평균으로 견준다(read_charadv.py).

    python exp/make_charadv.py ../out/oracle/d268.hwpx <출력 폴더>

앞 run = 「QZ」 + 글자 x16, 뒤 run = 글자 x16 + 「ZQ」. 원래 줄 배치는 지운다.
"""

import re
import sys
import zipfile
from pathlib import Path

CHARS = {
    "space": " ",
    "lparen": "(",
    "rparen": ")",
    "dot2027": "‧",
    "colon": ":",
    "arrow": "→",
    "comma": ",",
    "three": "3",
    "tri": "▶",
    "hangul": "인",
}
src, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
zin = zipfile.ZipFile(src)
parts = [(i.filename, i.compress_type, zin.read(i.filename)) for i in zin.infolist()]
SEG = re.compile(r"<hp:linesegarray>.*?</hp:linesegarray>", re.S)
OLD1 = "  ▶ 인센티브 부여 내용: "
OLD2 = "종합감사기간 축소(3일→2일), 특정‧복무감사 면제"
for name, ch in CHARS.items():
    with zipfile.ZipFile(out / f"c_{name}.hwpx", "w", zipfile.ZIP_DEFLATED) as z:
        for fname, ct, data in parts:
            if re.match(r"Contents/section\d+\.xml", fname):
                s = SEG.sub("", data.decode("utf-8"))
                if fname == "Contents/section1.xml":
                    assert s.count(OLD1) == 1 and s.count(OLD2) == 1
                    s = s.replace(OLD1, "QZ" + ch * 16).replace(OLD2, ch * 16 + "ZQ")
                data = s.encode("utf-8")
            z.writestr(zipfile.ZipInfo(fname), data, compress_type=ct)
print("ok", list(CHARS))
