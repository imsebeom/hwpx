"""양식 채우기 저장이 손대지 않은 문단의 줄 배치를 지우지 않는지 본다(2026-10-19).

종전 save() 는 문서 전체 줄 배치를 지우고 더미를 박아, 칸 몇 개만 채워도 rhwp, 에디터에서 다른 문단이
양쪽으로 벌어지고 쪽수가 늘었다. 이제 바꾼 칸, 새 행, 그 표를 담은 문단만 지운다.

    python tests/test_form_filler_linesegs.py
"""

import re
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from hwpx_form_filler import HwpxFormFiller  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "dense_table.hwpx"
DUMMY = 'horzsize="22960" flags="393216"'


def stats(path):
    s = zipfile.ZipFile(path).read("Contents/section0.xml").decode("utf-8")
    return s.count("<hp:p "), s.count("<hp:linesegarray"), s.count(DUMMY), s


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    n_p, n_lsa, n_dummy, _ = stats(FIXTURE)
    assert n_dummy == 0, "원본에 더미가 없어야 시험이 된다"
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "filled.hwpx"
        with HwpxFormFiller(str(FIXTURE)) as f:
            cells = f.analyze_table_structure(1)["content_cells"][:3]
            data = {(r, c): f"값{i}" for i, (r, c, _) in enumerate(cells)}
            data[(cells[0][0], cells[0][1])] = "첫 줄\n둘째 줄"
            assert f.fill_cells_directly(data, 1, skip_gate=True) == 3
            assert f.add_table_row(1, cells[0][0], None)
            f.save(str(out))
        p2, lsa2, dummy2, xml = stats(out)
    assert lsa2 == p2, f"줄 배치 없는 문단이 남았다({lsa2}/{p2})"
    # 바뀐 문단(칸 셋 + 여러 줄 + 새 행 + 표를 담은 문단 등)만 더미가 되고 나머지는 원래 줄 배치를 지킨다
    assert 0 < dummy2 < p2 // 4, (
        f"더미가 너무 많다({dummy2}/{p2}) — 문서 전체를 지운 것"
    )
    assert "첫 줄" in xml and "둘째 줄" in xml
    kept = len(re.findall(r'<hp:lineseg textpos="\d+" vertpos="\d+"', xml)) - dummy2
    print(f"문단 {p2}개 중 더미 {dummy2}개, 원래 줄 배치 유지 {kept}개")
    print("test_form_filler_linesegs: OK")


if __name__ == "__main__":
    main()
