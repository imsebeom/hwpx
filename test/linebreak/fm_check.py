"""font-metrics.mjs 가 읽은 폭을 fontTools 로 다시 읽어 대조한다."""

import json
import sys

from fontTools.ttLib import TTCollection, TTFont

sys.stdout.reconfigure(encoding="utf-8")
data = json.load(open("fm_dump.json", encoding="utf-8"))
total_bad = 0
for name, faces in data.items():
    for face in faces:
        path = face["file"]
        fonts = (
            TTCollection(path).fonts
            if path.lower().endswith(".ttc")
            else [TTFont(path)]
        )
        # ttc 안에서는 이름표에 그 글꼴 이름이 든 것을 고른다
        best = None
        for font in fonts:
            names = {
                r.toUnicode().strip().lower()
                for r in font["name"].names
                if r.nameID in (1, 4, 16)
            }
            if name.lower() in names:
                best = font
                break
        font = best or fonts[0]
        cmap, hmtx, upm = font.getBestCmap(), font["hmtx"], font["head"].unitsPerEm

        def adv(cp):
            return (
                (lambda w: 0 if w > 2 * upm else w)(hmtx[cmap[cp]][0])
                if cp in cmap
                else 0
            )

        bad = 0
        checked = 0
        if face["em"] != upm:
            bad += 1
        for start, widths in face["ranges"]:
            for i, w in enumerate(widths):
                checked += 1
                if adv(start + i) != w:
                    bad += 1
        hangul = face["hangul"]
        for k, cp in enumerate(range(0xAC00, 0xD7A4)):
            want = adv(cp)
            got = hangul[k] if isinstance(hangul, list) else (hangul or 0)
            checked += 1
            if want != got:
                bad += 1
        for start, end, w in face["uniform"]:
            for cp in range(start, end + 1):
                if cp in cmap:
                    checked += 1
                    if adv(cp) != w:
                        bad += 1
        total_bad += bad
        print(
            f"{name}{' 굵게' if face['bold'] else ''}: em {face['em']}, 한글 {'음절별' if isinstance(hangul, list) else hangul}, 대조 {checked}자, 다른 값 {bad}"
        )
print("다른 값 합계", total_bad)
