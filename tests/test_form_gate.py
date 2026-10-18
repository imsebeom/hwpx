"""양식 게이트의 템플릿 제작 판정(2026-10-19).

여러 줄 자리(「{{저서1}}\\n{{저서2}}」)와 원문 사이에 끼운 자리(「 □ 24호봉 이상」 → 「{{호봉24}} 24호봉 이상」)가
실제 값으로 오판돼 --skip-template-gate 로 우회해야 했다(다른 세션 보고 2026-10-18).

    python tests/test_form_gate.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from form_gate import is_template_write  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cases = [
        (["{{이름}}"], None, True),
        (["{{저서1}}\n{{저서2}}"], None, True),
        (["{{저서1}}\n\n{{저서2}}\n"], None, True),
        (["홍길동"], None, False),
        (["{{저서1}}\n실제 책 제목"], None, False),
        # 원문 사이에 끼운 자리: 원문을 알면 템플릿, 모르면 실제 값으로 본다
        (["{{호봉24}} 24호봉 이상"], " □ 24호봉 이상", True),
        (["{{호봉24}} 24호봉 이상"], None, False),
        # 원문에 없는 낱말이 붙으면 실제 값
        (["{{호봉24}} 홍길동"], " □ 24호봉 이상", False),
        (["", "  "], None, True),
    ]
    for values, original, want in cases:
        got = is_template_write(values, original)
        assert got == want, (values, original, got)
    print("test_form_gate: OK")


if __name__ == "__main__":
    main()
