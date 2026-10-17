"""개발용: HWP5 에서 온 HWPX(META-INF/rhwp-hwp5-origin)라도 본문 문단 전체에 줄 배치가 하나도 없으면 열 때 줄 배치를 다시 만든다.

    python apply_hwp5_origin_stripped.py [--revert]

근거(2026-10-18 사용자 보고 「끌어 선택하면 음영이 첫 줄에만, 끝 위치의 가로까지 칠해진다」, 가이드북 파트2간지_261018_11.hwpx):
그 문서는 hwp 변환 흔적 표지가 있는데, 스킬이 저장하며 linesegarray 를 모두 지웠다(문단 28개 중 줄 배치 0). 엔진은 표지가 있으면
빈 줄 배치를 HWP5 의 「진짜 빈 줄」로 보고 다시 만들지 않아 getLineStarts 가 빈 값이었다. 그리기는 따로 줄을 나눠 여러 줄로 보이지만,
선택 사각형과 커서 이동이 쓰는 줄 기록은 한 줄이라 음영이 첫 줄에 「시작 x ~ 끝 x」로만 칠해졌다.
HWP5 원본의 빈 줄 배치는 일부 문단에만 있으므로, 문서 전체가 비어 있으면 지운 캐시로 본다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx hwp5-origin-stripped]"

EDITS = [
    (
        "document_core/commands/document.rs",
        "        let hwp5_origin_hwpx = matches!(source_format, crate::parser::FileFormat::Hwpx)\n"
        "            && document\n"
        "                .hwpx_aux_entry(crate::model::document::HWP5_ORIGIN_HWPX_MARKER_PATH)\n"
        "                .is_some();\n",
        "        let hwp5_origin_hwpx = matches!(source_format, crate::parser::FileFormat::Hwpx)\n"
        "            && document\n"
        "                .hwpx_aux_entry(crate::model::document::HWP5_ORIGIN_HWPX_MARKER_PATH)\n"
        "                .is_some()\n"
        f"            // {TAG} 본문 문단 전체에 줄 배치가 하나도 없으면 HWP5 의 빈 줄이 아니라 지운 캐시다(스킬 저장본) — XML 처럼 다시 만든다\n"
        "            && document\n"
        "                .sections\n"
        "                .iter()\n"
        "                .flat_map(|section| section.paragraphs.iter())\n"
        "                .any(|para| !para.line_segs.is_empty());\n",
    ),
]


def main():
    revert = "--revert" in sys.argv
    edits = list(reversed(EDITS)) if revert else EDITS
    for rel, find, repl in edits:
        if revert:
            find, repl = repl, find
        f = SRC / rel
        raw = f.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        s = raw.replace("\r\n", "\n")
        if (find not in s) if revert else (repl in s):
            print("이미", rel)
            continue
        n = s.count(find)
        if n != 1:
            sys.exit(f"{rel}: 자리 {n}곳 — {find[:60]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel)


if __name__ == "__main__":
    main()
