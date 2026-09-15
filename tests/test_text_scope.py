"""치환 범위 회귀 테스트 — 규칙 41 (2026-09-15).

XML 전체 str.replace 가 속성값을 깨뜨리는 것을 재현하고, 기본(text) 범위는 속성을 건드리지 않으며
validate.py 가 깨진 파일을 잡는지 확인한다.

    python tests/test_text_scope.py
"""
import re
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from hwpx_helpers import replace_in_text_nodes, risky_replacement_keys  # noqa: E402
from validate import validate  # noqa: E402
from zip_replace_all import zip_replace_all  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "dense_table.hwpx"


def page_height(hwpx):
    s = zipfile.ZipFile(hwpx).read("Contents/section0.xml").decode("utf-8")
    return int(re.search(r'<hp:pagePr[^>]*height="(\d+)"', s).group(1))


def main():
    xml = '<hp:p id="17"><hp:run charPrIDRef="7"><hp:t>7회 중 17회</hp:t><hp:t>a<hp:tab/>7</hp:t></hp:run></hp:p>'
    out, n = replace_in_text_nodes(xml, {"7": "4", "17": "X"})
    assert out == '<hp:p id="17"><hp:run charPrIDRef="7"><hp:t>4회 중 X회</hp:t><hp:t>a<hp:tab/>4</hp:t></hp:run></hp:p>', out
    assert n == 4, n
    assert risky_replacement_keys({"7": "4", "4.2": "", "학교명": "x"}) == ["7", "4.2"]

    with tempfile.TemporaryDirectory() as d:
        text_out = Path(d) / "text.hwpx"
        raw_out = Path(d) / "raw.hwpx"
        h0 = page_height(FIXTURE)
        # 위험 키를 text 범위로 — 속성 무사, validate 통과
        zip_replace_all(FIXTURE, text_out, {"7": "4", "1417": "14"}, skip_gate=True)
        assert page_height(text_out) == h0, "text 범위가 pagePr 을 바꿨다"
        assert validate(str(text_out)) == [], validate(str(text_out))
        # 같은 키를 raw 로 — 속성이 깨지고 validate 가 잡는다
        zip_replace_all(FIXTURE, raw_out, {"7": "4", "1417": "14"}, skip_gate=True, scope="raw")
        errs = validate(str(raw_out))
        assert page_height(raw_out) != h0 or errs, "raw 치환이 속성을 바꾸지 않았다(픽스처에 7 이 없나?)"
        assert any("pagePr" in e or "격자" in e or "셀 주소" in e for e in errs), errs
    print("test_text_scope: OK")


if __name__ == "__main__":
    main()
