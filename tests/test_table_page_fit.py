"""표 쪽 나눔 판정 회귀 테스트 — 규칙 33 (2026-10-17).

적힌 hp:sz height만 믿으면 긴 표를 짧다고 보고 NONE을 권한다. NONE은 한 쪽보다 긴 표의 넘친 행을
그리지 않는다(한글 2024 실측: 40행 중 28행, 4행 중 2행만 렌더). 세 고정 파일로 판정을 확인한다.

- tall_cells_md2hwpx.hwpx: md2hwpx 산출물. 5행이지만 칸 글이 길어 실제로 4쪽. 적힌 높이 12,000
- long_table_hancom_saved.hwpx: 한글이 저장한 41행 표. 적힌 높이는 첫 쪽 조각 15,320
- short_table_md2hwpx.hwpx: 4행 짧은 표. 한 쪽에 들어가므로 NONE이 맞다
- tall_cells.md, short_table.md: md2hwpx_design 이 행 수만 보고 짧은 표를 NONE + 글자처럼 취급으로 두던 경로

    python tests/test_table_page_fit.py
"""

import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from table_page_fit import analyze  # noqa: E402

FIX = ROOT / "tests" / "fixtures"
CASES = [
    ("tall_cells_md2hwpx.hwpx", "TABLE"),
    ("long_table_hancom_saved.hwpx", "TABLE"),
    ("short_table_md2hwpx.hwpx", "NONE"),
]


DESIGN_CASES = [("tall_cells.md", "TABLE"), ("short_table.md", "NONE")]


def data_table_break(hwpx):
    """md2hwpx_design 산출물에서 R00 표지가 든 데이터 표의 pageBreak."""
    s = zipfile.ZipFile(hwpx).read("Contents/section0.xml").decode("utf-8")
    tbl = next(t for t in re.findall(r"<hp:tbl\b.*?</hp:tbl>", s, re.S) if "R00" in t)
    return re.search(r'pageBreak="(\w+)"', tbl).group(1)


def main():
    failed = 0
    with tempfile.TemporaryDirectory() as d:
        for name, want in DESIGN_CASES:
            out = Path(d) / (name + ".hwpx")
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "md2hwpx_design.py"),
                    str(FIX / name),
                    "-o",
                    str(out),
                ],
                check=True,
                capture_output=True,
            )
            got = data_table_break(out)
            ok = got == want
            failed += not ok
            print(
                f"{'PASS' if ok else 'FAIL'} md2hwpx_design {name}: 데이터 표 {got} (기대 {want})"
            )
    for name, want in CASES:
        plan = analyze(FIX / name)[0]
        ok = plan["recommend_pageBreak"] == want
        failed += not ok
        print(
            f"{'PASS' if ok else 'FAIL'} {name}: 높이 {plan['height']:,} / 본문 {plan['avail']:,} "
            f"→ {plan['recommend_pageBreak']} (기대 {want})"
        )
    if failed:
        sys.exit(1)
    print("모두 통과")


if __name__ == "__main__":
    main()
