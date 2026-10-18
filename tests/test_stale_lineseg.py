"""낡은 줄 배치 캐시 검사 회귀 테스트 — 규칙 17 (2026-10-17).

한글 2024 실측: 표 칸 문단의 글을 줄이고 <hp:linesegarray>를 두면 Open()이 False(대화상자 없음),
본문 문단은 한글이 다시 계산해 열린다. 실제 문서 243개 중 이 검사가 FAIL을 낸 4개는 모두 한글이 열지 못했고,
캐시를 지우니 열렸다.

- stale_cell_lineseg.hwpx: 칸 문단을 줄이고 캐시를 둠 → 오류
- stale_body_lineseg.hwpx: 본문 문단을 줄이고 캐시를 둠 → 경고
- long_table_hancom_saved.hwpx: 한글이 저장한 정상 문서 → 통과

    python tests/test_stale_lineseg.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from verify_hwpx import check_stale_lineseg  # noqa: E402

FIX = ROOT / "tests" / "fixtures"
CASES = [
    ("stale_cell_lineseg.hwpx", "error"),
    ("stale_body_lineseg.hwpx", "warning"),
    # 각주 안 문단 캐시가 글보다 뒤 → 한글 Open=False(2026-10-19), 폭만 다른 캐시는 열림
    ("stale_footnote_lineseg.hwpx", "error"),
    ("footnote_lineseg_width_only.hwpx", "pass"),
    ("long_table_hancom_saved.hwpx", "pass"),
]


def main():
    failed = 0
    for name, want in CASES:
        r = check_stale_lineseg(FIX / name)
        got = "error" if r["errors"] else "warning" if r["warnings"] else "pass"
        ok = got == want
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'} {name}: {got} (기대 {want})")
    if failed:
        sys.exit(1)
    print("모두 통과")


if __name__ == "__main__":
    main()
