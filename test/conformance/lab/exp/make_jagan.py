"""자간, 장평 줄 나눔 실험 사본: 빈 문서에 긴 문단 하나를 넣고 글자 모양 0 의 자간(spacing), 장평(ratio)만 바꾼다.

    python make_jagan.py <출력 폴더>

sp00..sp20 = 자간 0 ~ -20%(장평 100), ra100..ra80 = 장평 100 ~ 80%(자간 0, 2 간격). 줄 배치는 넣지 않는다(한/글, 엔진 모두 새로 조판).
"""

import os
import re
import sys
import zipfile
from pathlib import Path

BLANK = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / "blank.hwpx"
TEXT = (
    "교육과정 재구성은 학생의 삶과 배움을 잇는 일이다. 교사는 성취기준을 분석하고 학생의 흥미와 지역의 자원을 살펴 "
    "프로젝트의 흐름을 설계한다. 이 과정에서 인공지능 도구는 자료 탐색과 아이디어 발산을 돕지만, 판단과 성찰은 "
    "여전히 학생과 교사의 몫으로 남는다. 우리 학교는 3월부터 학년별 협의회를 열어 공통 주제를 정하고, 차시마다 "
    "학생이 스스로 질문을 만들고 답을 찾아가는 활동을 넣었다. 그 결과 학생들은 문제를 발견하고 해결 방법을 "
    "토의하며 결과물을 다듬는 경험을 쌓았고, 교사들은 수업 나눔으로 서로의 실천을 비교하며 다음 단원을 함께 준비했다."
)


def main(out):
    os.makedirs(out, exist_ok=True)
    zin = zipfile.ZipFile(BLANK)
    entries = [(it.filename, zin.read(it.filename)) for it in zin.infolist()]
    header = zin.read("Contents/header.xml").decode("utf-8")
    sec = zin.read("Contents/section0.xml").decode("utf-8")
    para = f'<hp:p id="1" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="0"><hp:t>{TEXT}</hp:t></hp:run></hp:p>'
    sec = sec.replace("</hs:sec>", para + "</hs:sec>")
    sec = re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", sec, flags=re.DOTALL)
    variants = {f"sp{-s:02d}": (s, 100) for s in range(0, -21, -1)}
    variants.update({f"ra{r}": (0, r) for r in range(100, 79, -2)})
    for name, (sp, ra) in variants.items():

        def fix(m, sp=sp, ra=ra):
            s = m.group(0)
            s = re.sub(
                r"<hh:ratio [^>]*/>",
                f'<hh:ratio hangul="{ra}" latin="{ra}" hanja="{ra}" japanese="{ra}" other="{ra}" symbol="{ra}" user="{ra}"/>',
                s,
            )
            return re.sub(
                r"<hh:spacing [^>]*/>",
                f'<hh:spacing hangul="{sp}" latin="{sp}" hanja="{sp}" japanese="{sp}" other="{sp}" symbol="{sp}" user="{sp}"/>',
                s,
            )

        h = re.sub(
            r'<hh:charPr id="0" .*?</hh:charPr>', fix, header, count=1, flags=re.DOTALL
        )
        with zipfile.ZipFile(os.path.join(out, name + ".hwpx"), "w") as z:
            # writestr 에 원본 ZipInfo 를 넘기면 크기 정보가 바뀌어 다음 판에서 원본을 못 읽는다 — 이름과 미리 읽은 바이트만 쓴다
            for fname, data in entries:
                if fname == "Contents/header.xml":
                    data = h.encode("utf-8")
                elif fname == "Contents/section0.xml":
                    data = sec.encode("utf-8")
                z.writestr(
                    fname,
                    data,
                    compress_type=zipfile.ZIP_STORED
                    if fname == "mimetype"
                    else zipfile.ZIP_DEFLATED,
                )


if __name__ == "__main__":
    main(sys.argv[1])
