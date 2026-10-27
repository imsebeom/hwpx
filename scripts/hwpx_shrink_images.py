#!/usr/bin/env python3
"""HWPX 그림 용량 줄이기.

한/글에 그림을 붙여 넣으면 BMP 원본이 그대로 들어가 문서가 수백 MB가 된다
(2026-10-27 교육력제고 결과보고서 255MB, BMP 46장이 압축 전 421MB).
그림마다 문서에서 실제로 보이는 크기(curSz, 잘라 낸 비율 imgClip/imgDim)를 읽어
목표 dpi에 맞춰 픽셀을 줄이고, BMP와 투명도 없는 큰 PNG는 JPEG로 바꾼다.

- imgDim, orgSz, imgClip은 HWPUNIT 좌표라 픽셀 수가 바뀌어도 그대로 맞는다.
- 형식이 바뀐 그림은 content.hpf의 href와 media-type만 고친다(id는 그대로라 본문 참조 불변).
- 본문 그림이 아닌 참조(header.xml의 채우기 그림 등)는 크기를 몰라 긴 변 --cap 픽셀로만 줄인다.

사용: python hwpx_shrink_images.py 입력.hwpx 출력.hwpx [--dpi 200] [--quality 88] [--cap 2000] [--min-side 800]
"""

import argparse
import io
import re
import sys
import zipfile

from PIL import Image

HWPUNIT_PER_INCH = 7200
PIC_RE = re.compile(r"<hp:pic\b.*?</hp:pic>", re.DOTALL)


def _num(pat, s, default=None):
    m = re.search(pat, s)
    return int(m.group(1)) if m else default


def required_inches(xmls):
    """그림 id → 보이는 크기를 원본 전체로 환산한 (가로, 세로) 인치의 최댓값."""
    need, other = {}, set()
    for s in xmls:
        for pic in PIC_RE.findall(s):
            ref = re.search(r'binaryItemIDRef="([^"]+)"', pic)
            if not ref:
                continue
            w = _num(r'<hp:curSz width="(\d+)"', pic, 0)
            h = _num(r'<hp:curSz width="\d+" height="(\d+)"', pic, 0)
            dw = _num(r'dimwidth="(\d+)"', pic)
            dh = _num(r'dimheight="(\d+)"', pic)
            cl = re.search(
                r'<hp:imgClip left="(-?\d+)" right="(-?\d+)" top="(-?\d+)" bottom="(-?\d+)"',
                pic,
            )
            fx = fy = 1.0
            if cl and dw and dh:
                left, right, top, bottom = map(int, cl.groups())
                fx = max((right - left) / dw, 0.05)
                fy = max((bottom - top) / dh, 0.05)
            if not w or not h:
                other.add(
                    ref.group(1)
                )  # 크기 0으로 적힌 참조는 믿지 않는다(1x1로 줄던 일)
                continue
            iw = w / HWPUNIT_PER_INCH / min(fx, 1.0)
            ih = h / HWPUNIT_PER_INCH / min(fy, 1.0)
            ow, oh = need.get(ref.group(1), (0, 0))
            need[ref.group(1)] = (max(ow, iw), max(oh, ih))
        # 그림 개체 밖의 참조(채우기 그림 등)
        outside = PIC_RE.sub("", s)
        other.update(re.findall(r'binaryItemIDRef="([^"]+)"', outside))
    return need, other


def has_real_alpha(im):
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        return im.convert("RGBA").getchannel("A").getextrema()[0] < 255
    return False


def shrink(data, ext, inches, dpi, quality, cap, min_side):
    """(새 바이트, 새 확장자, 설명) 또는 None(그대로 둔다)."""
    im = Image.open(io.BytesIO(data))
    im.load()
    exif = im.info.get("exif")
    pw, ph = im.size
    if inches:
        iw, ih = inches
        # 90도 회전해 놓은 경우를 대비해 두 방향 모두로 요구를 재고 큰 쪽을 쓴다
        sx = max(iw * dpi / pw, ih * dpi / ph, ih * dpi / pw, iw * dpi / ph)
    else:
        sx = cap / max(pw, ph)
    # 화면에서 확대해 보아도 견디게 긴 변은 min_side 픽셀 아래로 내리지 않는다
    sx = max(sx, min_side / max(pw, ph))
    scale = min(1.0, sx)
    alpha = has_real_alpha(im)
    to_jpeg = ext == "bmp" or (ext == "png" and not alpha and len(data) > 300_000)
    if scale > 0.9 and not to_jpeg:
        return None
    if scale < 1.0:
        im = im.resize(
            (max(1, round(pw * scale)), max(1, round(ph * scale))), Image.LANCZOS
        )
    buf = io.BytesIO()
    if to_jpeg or ext in ("jpg", "jpeg"):
        kw = {"quality": quality, "optimize": True}
        if exif:
            kw["exif"] = exif
        im.convert("RGB").save(buf, "JPEG", **kw)
        new_ext = "jpg"
    else:
        im.save(buf, "PNG", optimize=True)
        new_ext = ext
    if len(buf.getvalue()) >= len(data) and new_ext == ext:
        return None
    return buf.getvalue(), new_ext, f"{pw}x{ph} → {im.size[0]}x{im.size[1]}"


MEDIA = {"jpg": "image/jpg", "png": "image/png"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--quality", type=int, default=88)
    ap.add_argument("--cap", type=int, default=2000)
    ap.add_argument("--min-side", type=int, default=800)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    zin = zipfile.ZipFile(a.src)
    names = zin.namelist()
    xmls = [
        zin.read(n).decode("utf-8")
        for n in names
        if n.startswith("Contents/") and n.endswith(".xml")
    ]
    need, other = required_inches(xmls)
    hpf = zin.read("Contents/content.hpf").decode("utf-8")
    jpg_media = re.search(r'media-type="(image/jpe?g)"', hpf)
    MEDIA["jpg"] = jpg_media.group(1) if jpg_media else "image/jpeg"

    renamed, out_bin, before, after = {}, {}, 0, 0
    for n in names:
        if not n.startswith("BinData/"):
            continue
        stem, ext = n[len("BinData/") :].rsplit(".", 1)
        ext = ext.lower()
        if ext not in ("bmp", "png", "jpg", "jpeg"):
            continue
        data = zin.read(n)
        before += len(data)
        if stem not in need and stem not in other:
            after += len(data)
            continue  # 쓰이지 않는 그림은 건드리지 않는다
        try:
            r = shrink(data, ext, need.get(stem), a.dpi, a.quality, a.cap, a.min_side)
        except OSError as e:
            print(f"  건너뜀 {n}: {e}")
            r = None
        if not r:
            after += len(data)
            continue
        new, new_ext, note = r
        after += len(new)
        new_name = f"BinData/{stem}.{new_ext}"
        out_bin[n] = (new_name, new)
        if new_name != n:
            renamed[stem] = (n, new_name, new_ext)
        if len(data) > 2_000_000:
            print(f"  {n} {len(data) / 1e6:.1f}MB → {len(new) / 1e6:.2f}MB ({note})")

    for stem, (old, new, new_ext) in renamed.items():
        pat = re.compile(
            r'(<opf:item id="'
            + re.escape(stem)
            + r'" href=")'
            + re.escape(old)
            + r'(" media-type=")[^"]+(")'
        )
        hpf, k = pat.subn(r"\g<1>" + new + r"\g<2>" + MEDIA[new_ext] + r"\g<3>", hpf)
        if k != 1:
            sys.exit(f"content.hpf에서 {stem} 항목을 하나로 찾지 못했다({k}개)")

    with zipfile.ZipFile(a.dst, "w") as zout:
        for info in zin.infolist():
            n = info.filename
            if n == "Contents/content.hpf":
                zout.writestr(info, hpf.encode("utf-8"))
            elif n in out_bin:
                new_name, new = out_bin[n]
                ni = zipfile.ZipInfo(new_name, info.date_time)
                ni.compress_type = zipfile.ZIP_DEFLATED
                ni.external_attr = info.external_attr
                zout.writestr(ni, new)
            else:
                zout.writestr(info, zin.read(n))
    print(
        f"그림 {len(out_bin)}개 줄임(형식 변경 {len(renamed)}개): "
        f"{before / 1e6:.1f}MB → {after / 1e6:.1f}MB"
    )


if __name__ == "__main__":
    main()
