"""큰 hwpx 를 에디터로 열 수 있게 그림만 줄인 보기용 사본을 만든다.

    python image_proxy.py <원본.hwpx> <사본.hwpx> <대응표.json> [--max 1200] [--quality 80] [--min-kb 200]

- 그림(BinData)이 min-kb 보다 크면 긴 변을 max px 이하로 줄여 JPEG 로 바꾼다. 이름은 확장자만 .jpg 로,
  content.hpf 의 href 와 media-type 도 함께 바꾼다(본문은 binaryItemIDRef=항목 id 로 가리키므로 그대로다).
- 대응표에 사본 그림의 sha1 과 원본 이름, media-type, hashkey 를 적는다. 저장할 때 image-proxy.mjs 가
  이것으로 줄인 그림을 원본으로 되돌린다.
- 원본 파일은 읽기만 한다.
"""

import argparse
import hashlib
import io
import json
import re
import sys
import zipfile

from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")


def to_jpeg(data: bytes, max_px: int, quality: int) -> bytes | None:
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
    except Exception:
        return None
    if im.mode in ("RGBA", "LA", "P", "PA"):
        rgba = im.convert("RGBA")
        bg = Image.new("RGB", im.size, "white")
        bg.paste(rgba, mask=rgba.split()[-1])
        im = bg
    else:
        im = im.convert("RGB")
    im.thumbnail((max_px, max_px))
    out = io.BytesIO()
    im.save(out, "JPEG", quality=quality)
    return out.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("map")
    ap.add_argument("--max", type=int, default=1200)
    ap.add_argument("--quality", type=int, default=80)
    ap.add_argument("--min-kb", type=int, default=200)
    a = ap.parse_args()

    zin = zipfile.ZipFile(a.src)
    names = set(zin.namelist())
    hpf = zin.read("Contents/content.hpf").decode("utf-8")
    renamed, table = {}, []
    before = after = 0
    for info in zin.infolist():
        n = info.filename
        if not n.startswith("BinData/") or info.file_size < a.min_kb * 1024:
            continue
        data = zin.read(info)
        jpg = to_jpeg(data, a.max, a.quality)
        if jpg is None or len(jpg) >= len(data):
            continue
        new = re.sub(r"\.[^./]+$", "", n) + ".jpg"
        if new != n and new in names:
            new = re.sub(r"\.[^./]+$", "", n) + "_proxy.jpg"
        item = re.search(rf'<opf:item [^>]*href="{re.escape(n)}"[^>]*/>', hpf)
        if not item:
            continue
        mt = re.search(r'media-type="([^"]*)"', item.group(0))
        hk = re.search(r'hashkey="([^"]*)"', item.group(0))
        new_item = item.group(0).replace(f'href="{n}"', f'href="{new}"')
        if mt:
            new_item = new_item.replace(mt.group(0), 'media-type="image/jpg"')
        hpf = hpf.replace(item.group(0), new_item)
        renamed[n] = (new, jpg)
        table.append(
            {
                "proxy": new,
                "sha1": hashlib.sha1(jpg).hexdigest(),
                "orig": n,
                "mediaType": mt.group(1) if mt else None,
                "hashkey": hk.group(1) if hk else None,
            }
        )
        before += len(data)
        after += len(jpg)

    with zipfile.ZipFile(a.dst, "w") as zout:
        for info in zin.infolist():
            n = info.filename
            if n in renamed:
                zout.writestr(
                    zipfile.ZipInfo(renamed[n][0], info.date_time),
                    renamed[n][1],
                    zipfile.ZIP_DEFLATED,
                )
            elif n == "Contents/content.hpf":
                zout.writestr(info, hpf.encode("utf-8"), info.compress_type)
            else:
                zout.writestr(info, zin.read(info), info.compress_type)
    with open(a.map, "w", encoding="utf-8") as f:
        json.dump({"src": a.src, "max": a.max, "images": table}, f, ensure_ascii=False)
    print(
        json.dumps(
            {
                "images": len(table),
                "beforeMB": round(before / 1e6, 1),
                "afterMB": round(after / 1e6, 1),
            }
        )
    )


if __name__ == "__main__":
    main()
