"""zip_replace_all 회귀 시험(2026-10-19).

1. 글이 바뀐 문단만 줄 배치를 지운다. 칸 글을 줄이고 옛 캐시를 두면 한글이 열지 못했다
   (dense_table 칸 글 두 개를 짧게 바꾼 사본이 Open False, 고친 뒤 True).
2. 게이트에 막히면 임시 출력(hwpx-replace-*.hwpx)을 남기지 않는다.

    python tests/test_zip_replace_linesegs.py
"""

import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import zip_replace_all as zr  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "dense_table.hwpx"
LONG = "해당 차시에 적절한 모형이 있으면 모형의 단계에 맞추어 설계하되, 알맞은 모형이 없을 시 생략할 수 있음."


def section(path):
    return zipfile.ZipFile(path).read("Contents/section0.xml").decode("utf-8")


def para_of(xml, needle):
    """needle 을 직접 담은 가장 안쪽 문단 문자열"""
    i = xml.index(needle)
    a = xml.rfind("<hp:p ", 0, i)
    b = xml.index("</hp:p>", i)
    return xml[a:b]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    before = section(FIXTURE)
    assert "<hp:linesegarray" in para_of(before, LONG), (
        "원본 문단에 줄 배치가 있어야 시험이 된다"
    )
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.hwpx"
        st = zr.zip_replace_all(FIXTURE, out, {LONG: "짧음"}, skip_gate=True)
        assert st["replacements"] == 1 and st["lineseg_dropped"] == 1, st
        after = section(out)
        p = para_of(after, "짧음")
        assert 'horzsize="22960" flags="393216"' in p, (
            "바뀐 문단은 옛 줄 배치 대신 더미여야 한다"
        )
        # 손대지 않은 문단의 실제 줄 배치는 그대로
        other = "해당 교과 교육과정에서 해당 차시의 성취기준으로 작성"
        assert para_of(before, other) == para_of(after, other)

        # 게이트 차단 시 임시 파일이 남지 않는다(--inplace 는 임시 출력을 먼저 만든다)
        work = Path(tmp) / "gate"
        work.mkdir()
        target = work / "form.hwpx"
        shutil.copy(FIXTURE, target)
        rc = zr.main([str(target), "--inplace", "--replace", f"{LONG}=실제 값"])
        assert rc == 2, rc
        left = sorted(x.name for x in work.iterdir())
        assert left == ["form.hwpx"], left
    print("test_zip_replace_linesegs: OK")


if __name__ == "__main__":
    main()
