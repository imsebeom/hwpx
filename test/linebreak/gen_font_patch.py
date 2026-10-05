"""설치된 글꼴 파일의 전진 폭(hmtx)으로 rhwp 폭 자료 패치(patches/font-metrics-extra.rs)를 만든다.

    python gen_font_patch.py <출력 .rs>

rhwp 는 폭 자료가 없는 글꼴을 한글 1.0em, 그 밖 0.5em 으로 어림한다. 한/글은 글꼴 파일의 폭을 쓰므로
(2026-10-06 사다리 84건 일치) 줄 나눔이 어긋난다. 여기서 뽑는 것은 글자별 전진 폭 숫자뿐이고 글꼴 파일은 싣지 않는다.
패치는 src/renderer/font_metrics_overlays.rs 의 MEASURED_FONT_METRIC_OVERLAYS 배열에 항목을 덧붙인다.
"""

import os
import sys
from collections import Counter

from fontTools.ttLib import TTFont

sys.stdout.reconfigure(encoding="utf-8")
WIN = r"C:\Windows\Fonts"
USER = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts")
BASE_COUNT = 8  # rhwp v0.8.6 의 MEASURED_FONT_METRIC_OVERLAYS 항목 수

# 얼굴 키 → 글꼴 파일
FACES = {
    "HANSANTTEUT_R": os.path.join(WIN, "HanSantteutDotum-Regular.ttf"),
    "HANSANTTEUT_B": os.path.join(WIN, "HanSantteutDotum-Bold.ttf"),
    "HANCOMGOTHIC_R": os.path.join(WIN, "Hancom Gothic Regular.ttf"),
    "HANCOMGOTHIC_B": os.path.join(WIN, "Hancom Gothic Bold.ttf"),
    "NANUMSQUARE_R": os.path.join(USER, "NanumSquareR.ttf"),
    "NANUMSQUARE_B": os.path.join(USER, "NanumSquareB.ttf"),
    "NANUMSQUARE_EB": os.path.join(USER, "NanumSquareEB.ttf"),
    "NANUMSQUARE_L": os.path.join(USER, "NanumSquareL.ttf"),
}
# (문서에 적히는 글꼴 이름, 굵게, 얼굴 키). 이름은 정확히 일치해야 한다.
# 한컴 두 글꼴은 굵은 글씨가 같은 가족의 굵은 얼굴이고, 나눔스퀘어는 굵기마다 가족 이름이 따로다.
ENTRIES = [
    ("한컴산뜻돋움", False, "HANSANTTEUT_R"),
    ("한컴산뜻돋움", True, "HANSANTTEUT_B"),
    ("Han Santteut Dotum", False, "HANSANTTEUT_R"),
    ("Han Santteut Dotum", True, "HANSANTTEUT_B"),
    ("한컴 고딕", False, "HANCOMGOTHIC_R"),
    ("한컴 고딕", True, "HANCOMGOTHIC_B"),
    ("Hancom Gothic", False, "HANCOMGOTHIC_R"),
    ("Hancom Gothic", True, "HANCOMGOTHIC_B"),
    ("나눔스퀘어", False, "NANUMSQUARE_R"),
    ("NanumSquare", False, "NANUMSQUARE_R"),
    ("나눔스퀘어 Bold", False, "NANUMSQUARE_B"),
    ("NanumSquare Bold", False, "NANUMSQUARE_B"),
    ("나눔스퀘어 ExtraBold", False, "NANUMSQUARE_EB"),
    ("NanumSquare ExtraBold", False, "NANUMSQUARE_EB"),
    ("나눔스퀘어 Light", False, "NANUMSQUARE_L"),
    ("NanumSquare Light", False, "NANUMSQUARE_L"),
]
# 폭을 싣는 구간. 한글 음절은 단일 폭으로 따로 싣고, 한자는 싣지 않는다(없으면 엔진이 1.0em 으로 어림).
BLOCKS = [
    (0x0020, 0x007E),  # ASCII
    (0x00A0, 0x00FF),  # 라틴-1(가운뎃점 등)
    (0x2000, 0x206F),  # 일반 문장 부호(따옴표, 줄임표, 참고표)
    (0x2100, 0x27BF),  # 글자꼴 기호, 로마 숫자, 화살표, 수학, 원 숫자, 괘선, 도형, 딩뱃
    (0x3000, 0x303F),  # CJK 문장 부호(낫표)
    (0x3130, 0x318F),  # 한글 호환 자모
    (0x3200, 0x33FF),  # 원 한글, 단위 기호
    (0xFF00, 0xFFEF),  # 전각, 반각 꼴
]


def load(path):
    font = TTFont(path)
    cmap, hmtx, upm = font.getBestCmap(), font["hmtx"], font["head"].unitsPerEm
    # 폭이 em 의 두 배를 넘는 글리프는 깨진 값(음수의 16비트 표현)이라 없는 것으로 친다
    adv = {cp: (hmtx[g][0] if hmtx[g][0] <= 2 * upm else 0) for cp, g in cmap.items()}
    syllables = Counter(adv.get(cp, 0) for cp in range(0xAC00, 0xD7A4))
    width, count = syllables.most_common(1)[0]
    assert count == 11172, (
        f"{path}: 한글 음절 폭이 균일하지 않다 {syllables.most_common(3)}"
    )
    ranges = []
    for start, end in BLOCKS:
        widths = [adv.get(cp, 0) for cp in range(start, end + 1)]
        while widths and widths[-1] == 0:
            widths.pop()
        if any(widths):
            ranges.append((start, start + len(widths) - 1, tuple(widths)))
    return {"upm": upm, "hangul": width, "ranges": ranges}


def main(out_path):
    faces = {key: load(path) for key, path in FACES.items()}
    arrays = {}  # 폭 배열 → 이름(같은 배열은 한 번만 싣는다)
    lines = [
        "// [claude-hwpx font-metrics-extra] 한컴산뜻돋움, 한컴 고딕, 나눔스퀘어의 글자 폭.",
        "// 설치된 글꼴 파일의 hmtx 전진 폭을 그대로 옮겼다(test/linebreak/gen_font_patch.py 가 만든다, 손으로 고치지 않는다).",
        "// 한/글 2024 폭 사다리 84건(2026-10-06)이 이 값에 4 HWPUNIT 규칙을 적용한 것과 모두 일치했다.",
        "// 종전에는 자료가 없어 한글 1.0em(실제 0.932, 0.910), 그 밖 0.5em 으로 어림해 줄을 한/글보다 덜 담았다.",
    ]
    for key, face in faces.items():
        refs = []
        for start, end, widths in face["ranges"]:
            if widths not in arrays:
                arrays[widths] = f"CLAUDE_FM_W{len(arrays)}"
                body = ", ".join(str(w) for w in widths)
                lines.append(
                    f"static {arrays[widths]}: [u16; {len(widths)}] = [{body}];"
                )
            refs.append(
                f"LatinRange {{ start: 0x{start:04X}, end: 0x{end:04X}, widths: &{arrays[widths]} }}"
            )
        lines.append(f"static CLAUDE_FM_{key}_RANGES: [LatinRange; {len(refs)}] = [")
        lines += [f"    {r}," for r in refs]
        lines.append("];")
        lines.append(
            f"static CLAUDE_FM_{key}_HANGUL_WIDTHS: [u16; 1] = [{face['hangul']}];"
        )
        lines.append(
            f"static CLAUDE_FM_{key}_HANGUL: HangulMetric = HangulMetric {{ cho_groups: 1, jung_groups: 1, jong_groups: 1, "
            f"cho_map: &FONT_0_HANGUL_CHO, jung_map: &FONT_0_HANGUL_JUNG, jong_map: &FONT_0_HANGUL_JONG, "
            f"widths: &CLAUDE_FM_{key}_HANGUL_WIDTHS }};"
        )
    head = f"static MEASURED_FONT_METRIC_OVERLAYS: [FontMetric; {BASE_COUNT}] = ["
    new_head = f"static MEASURED_FONT_METRIC_OVERLAYS: [FontMetric; {BASE_COUNT + len(ENTRIES)}] = ["
    tail = "        latin_ranges: &HANYOONGOTHIC760_LATIN_RANGES,\n        hangul: Some(&HANYOONGOTHIC760_HANGUL),\n    },\n];"
    entries = []
    for name, bold, key in ENTRIES:
        entries.append(
            f'    FontMetric {{ name: "{name}", bold: {str(bold).lower()}, italic: false, em_size: {faces[key]["upm"]}, '
            f"latin_ranges: &CLAUDE_FM_{key}_RANGES, hangul: Some(&CLAUDE_FM_{key}_HANGUL) }},"
        )
    patch = "\n".join(
        [
            "// ==== find ====",
            head,
            "// ==== replace ====",
            *lines,
            new_head,
            "// ==== next ====",
            tail,
            "// ==== replace ====",
            tail[: -len("];")].rstrip("\n"),
            "    // 한컴산뜻돋움, 한컴 고딕, 나눔스퀘어 — 문서에 적히는 이름 그대로(영문 이름도 함께)",
            *entries,
            "];",
        ]
    )
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(patch + "\n")
    print(
        f"얼굴 {len(faces)}개, 폭 배열 {len(arrays)}개, 항목 {len(ENTRIES)}개, {os.path.getsize(out_path):,}바이트 → {out_path}"
    )
    for key, face in faces.items():
        print(
            f"  {key}: 한글 {face['hangul']}/{face['upm']}, 구간 {[(hex(s), e - s + 1) for s, e, _ in face['ranges']]}"
        )


if __name__ == "__main__":
    main(sys.argv[1])
