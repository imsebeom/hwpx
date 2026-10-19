"""엔진 SVG 의 글자 요소에서 위치를 읽는다(exp/rendery.py, charwidth.py, read_charcal.py 공용).

장평 100% 글자는 x, y 속성이고, 장평이 다르면 transform="translate(x,y) scale(sx,1)" 이다.
"""

import re

TEXT = re.compile(r"<text\b([^>]*)>([^<]*)</text>")
_X = re.compile(r'\bx="([-\d.]+)"')
_Y = re.compile(r'\by="([-\d.]+)"')
_TR = re.compile(r'transform="translate\(([-\d.]+),\s*([-\d.]+)\)')


def text_xy(attrs):
    """속성 문자열 → (x, y) px 또는 None"""
    m = _TR.search(attrs)
    if m:
        return float(m.group(1)), float(m.group(2))
    xm, ym = _X.search(attrs), _Y.search(attrs)
    if xm and ym:
        return float(xm.group(1)), float(ym.group(1))
    return None
