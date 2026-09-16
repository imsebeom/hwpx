"""
범용 HWPX N-파일 병합기 (이종 템플릿, 첫 파일 기반 이어쓰기).

첫 번째 파일을 고정 기반으로 두고 header·section·settings·META-INF를 그대로 유지한다.
두 번째 파일부터는 각 추가 파일의 header 항목(charPr/paraPr/borderFill)을 기반 파일
header에 offset 방식으로 통합하고, 해당 파일의 section 문단을 리맵해서 기반 section
끝에 순차 이어붙인다. 서로 다른 템플릿에서 만든 HWPX를 스타일 보존하며 병합할 수 있다.

누적 병합(2-file 호출 반복)의 ID 공간 혼재 문제를 피하기 위해, N개 파일을 한 번의
pass에서 처리한다.

Usage:
    python merge_hwpx.py <file1.hwpx> <file2.hwpx> [<file3.hwpx> ...] -o <output.hwpx>
        [--no-pagebreak]
        [--img-prefix-tpl TEMPLATE]    기본 "s{idx}_" (idx는 2번 파일부터 1부터 증가)

관례:
  - 첫 파일의 secPr/ctrl은 그대로 유지 (문서 섹션 설정)
  - 추가 파일의 선두 문단이 secPr/ctrl을 포함하면 그 요소만 제거, 나머지 콘텐츠
    (예: 부서명·제목·표)는 보존하고 본체에 이어붙임
  - 추가 파일의 paraPr 내 <hh:border>와 charPr의 borderFillIDRef는 안전한 기본값
    "1"로 고정 (뷰어가 type=NONE이어도 박스 테두리를 렌더링하는 이슈 방지)
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import zipfile
from copy import deepcopy
from pathlib import Path

from lxml import etree

sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"
HH = "http://www.hancom.co.kr/hwpml/2011/head"
HC = "http://www.hancom.co.kr/hwpml/2011/core"

LANG_TO_ATTR = {
    "HANGUL": "hangul", "LATIN": "latin", "HANJA": "hanja",
    "JAPANESE": "japanese", "OTHER": "other", "SYMBOL": "symbol", "USER": "user",
}


# ==================== 헬퍼 ====================

def find_items(header, tag):
    items = []
    for elem in header.iter(f"{{{HH}}}{tag}"):
        v = elem.get("id")
        if v is not None and v.isdigit():
            items.append((int(v), elem))
    return items


def get_max_id(root):
    mx = 0
    for elem in root.iter():
        v = elem.get("id")
        if v and v.isdigit():
            mx = max(mx, int(v))
    return mx


def count_skip(paras):
    """secPr/ctrl이 포함된 선두 문단 수 (문단 자체는 보존, 그 내부만 정리)."""
    skip = 0
    for p in paras:
        if (p.find(f".//{{{HP}}}secPr") is not None
                or p.find(f".//{{{HP}}}ctrl") is not None):
            skip += 1
        else:
            break
    return skip


def build_font_map(header_src, header_tgt):
    """src의 fontRef id → tgt의 동일 이름 fontRef id (lang별)."""
    font_map = {}
    for ff_tgt in header_tgt.iter(f"{{{HH}}}fontface"):
        lang = ff_tgt.get("lang")
        name_to_id = {f.get("face"): f.get("id")
                      for f in ff_tgt.iter(f"{{{HH}}}font")}
        for ff_src in header_src.iter(f"{{{HH}}}fontface"):
            if ff_src.get("lang") == lang:
                for f in ff_src.iter(f"{{{HH}}}font"):
                    if f.get("face") in name_to_id:
                        font_map[(lang, f.get("id"))] = name_to_id[f.get("face")]
    return font_map


def make_pagebreak_para(pid):
    p = etree.Element(f"{{{HP}}}p", nsmap={"hp": HP})
    p.set("id", str(pid))
    p.set("paraPrIDRef", "0")
    p.set("styleIDRef", "0")
    p.set("pageBreak", "1")
    p.set("columnBreak", "0")
    p.set("merged", "0")
    run = etree.SubElement(p, f"{{{HP}}}run")
    run.set("charPrIDRef", "0")
    etree.SubElement(run, f"{{{HP}}}t")
    return p


# ==================== header 통합 ====================

def integrate_header(header_tgt, header_src):
    """src header 항목을 tgt header에 offset으로 추가.

    반환: (cp_map, pp_map, bf_map) — src id → tgt id 매핑 테이블.
    """
    max_cp = max((i for i, _ in find_items(header_tgt, "charPr")), default=-1)
    max_pp = max((i for i, _ in find_items(header_tgt, "paraPr")), default=-1)
    max_bf = max((i for i, _ in find_items(header_tgt, "borderFill")), default=-1)

    font_map = build_font_map(header_src, header_tgt)

    # borderFill 먼저 추가 (charPr/paraPr이 borderFillIDRef 참조 가능)
    bf_map = {}
    bf_container = header_tgt.find(f".//{{{HH}}}borderFills")
    for old_id, elem in find_items(header_src, "borderFill"):
        new_id = max_bf + 1 + old_id
        bf_map[old_id] = new_id
        new_elem = deepcopy(elem)
        new_elem.set("id", str(new_id))
        bf_container.append(new_elem)
    bf_container.set("itemCnt", str(len(list(bf_container))))

    # charPr 추가 — 자체 borderFillIDRef는 "1"로 강제, fontRef는 이름 매핑
    cp_map = {}
    cp_container = header_tgt.find(f".//{{{HH}}}charProperties")
    for old_id, elem in find_items(header_src, "charPr"):
        new_id = max_cp + 1 + old_id
        cp_map[old_id] = new_id
        new_elem = deepcopy(elem)
        new_elem.set("id", str(new_id))
        new_elem.set("borderFillIDRef", "1")  # 박스 테두리 렌더링 방지
        fr = new_elem.find(f"{{{HH}}}fontRef")
        if fr is not None:
            for lang, attr in LANG_TO_ATTR.items():
                old_fid = fr.get(attr)
                if old_fid and (lang, old_fid) in font_map:
                    fr.set(attr, font_map[(lang, old_fid)])
        cp_container.append(new_elem)
    cp_container.set("itemCnt", str(len(list(cp_container))))

    # paraPr 추가 — 내부 <hh:border>의 borderFillIDRef는 "1"로 강제
    pp_map = {}
    pp_container = header_tgt.find(f".//{{{HH}}}paraProperties")
    for old_id, elem in find_items(header_src, "paraPr"):
        new_id = max_pp + 1 + old_id
        pp_map[old_id] = new_id
        new_elem = deepcopy(elem)
        new_elem.set("id", str(new_id))
        for border in new_elem.iter(f"{{{HH}}}border"):
            border.set("borderFillIDRef", "1")
        pp_container.append(new_elem)
    pp_container.set("itemCnt", str(len(list(pp_container))))

    return cp_map, pp_map, bf_map


# ==================== section 리맵 + 이어쓰기 ====================

def _strip_section_control(para):
    """문단 내부의 <hp:secPr>/<hp:ctrl> 요소를 제거하고 빈 run을 정리한다.

    문단 자체는 보존하므로 같은 문단에 들어있던 <hp:tbl>·본문 run 등은 남는다.
    """
    for el in list(para.iter()):
        local = etree.QName(el).localname
        if local in ("secPr", "ctrl"):
            parent = el.getparent()
            if parent is not None:
                parent.remove(el)
    for run in list(para.iter(f"{{{HP}}}run")):
        if len(run) == 0 and not (run.text or "").strip():
            parent = run.getparent()
            if parent is not None:
                parent.remove(run)


def remap_and_append_section(root_tgt, root_src, cp_map, pp_map, bf_map,
                             img_prefix, pid_start, pagebreak=True):
    """src section 문단을 리맵해서 tgt section 끝에 추가. 마지막 pid 반환."""
    # *IDRef 리맵
    for elem in root_src.iter():
        cp = elem.get("charPrIDRef")
        if cp and cp.isdigit() and int(cp) in cp_map:
            elem.set("charPrIDRef", str(cp_map[int(cp)]))
        pp = elem.get("paraPrIDRef")
        if pp and pp.isdigit() and int(pp) in pp_map:
            elem.set("paraPrIDRef", str(pp_map[int(pp)]))
        bf = elem.get("borderFillIDRef")
        if bf and bf.isdigit() and int(bf) in bf_map:
            elem.set("borderFillIDRef", str(bf_map[int(bf)]))
        if elem.get("styleIDRef") is not None and elem.get("styleIDRef") != "0":
            elem.set("styleIDRef", "0")
        ref = elem.get("binaryItemIDRef")
        if ref:
            # BinData 파일명과 content.hpf 항목에는 접두어가 무조건 붙으므로
            # 참조도 이름을 가리지 않고 함께 붙여야 한다. "image"로 시작하는 것만
            # 붙이던 때에는 직접 지은 id(r02_1 등)의 그림이 통째로 사라졌다 (2026-09-16)
            elem.set("binaryItemIDRef", img_prefix + ref)

    pid = pid_start
    if pagebreak:
        pid += 1
        root_tgt.append(make_pagebreak_para(pid))

    src_paras = list(root_src)
    skip = count_skip(src_paras)
    for i, para in enumerate(src_paras):
        new_para = deepcopy(para)
        if i < skip:
            _strip_section_control(new_para)
        pid += 1
        new_para.set("id", str(pid))
        root_tgt.append(new_para)
    return pid


# ==================== 공개 API ====================

def merge_hwpx(files, output, pagebreak=True, img_prefix_tpl="s{idx}_"):
    """N개의 HWPX 파일을 병합한다 (첫 파일 기반, 나머지를 순차 이어쓰기).

    Args:
        files: HWPX 파일 경로 리스트 (2개 이상). files[0]이 고정 기반.
        output: 출력 HWPX 파일 경로.
        pagebreak: True면 추가 파일 앞에 페이지 넘김 문단 삽입.
        img_prefix_tpl: 이미지 접두어 템플릿. `{idx}`는 1,2,3… 으로 치환.
    """
    files = [Path(f) for f in files]
    output = Path(output)
    if len(files) < 2:
        raise ValueError("최소 2개 파일이 필요합니다")

    base_path = files[0]
    print(f"기반: {base_path.name}")

    with zipfile.ZipFile(str(base_path)) as z:
        header_tgt = etree.fromstring(z.read("Contents/header.xml"))
        root_tgt = etree.fromstring(z.read("Contents/section0.xml"))
        base_hpf = z.read("Contents/content.hpf").decode("utf-8")
        all_bindata = {n: z.read(n) for n in z.namelist()
                       if n.startswith("BinData/")}

    pid = get_max_id(root_tgt) + 1000

    for idx, src_path in enumerate(files[1:], start=1):
        img_prefix = img_prefix_tpl.format(idx=idx)
        print(f"[{idx}/{len(files)-1}] {src_path.name} (prefix={img_prefix})")
        with zipfile.ZipFile(str(src_path)) as z:
            header_src = etree.fromstring(z.read("Contents/header.xml"))
            root_src = etree.fromstring(z.read("Contents/section0.xml"))
            src_bindata = {n: z.read(n) for n in z.namelist()
                           if n.startswith("BinData/")}

        cp_map, pp_map, bf_map = integrate_header(header_tgt, header_src)
        pid = remap_and_append_section(root_tgt, root_src,
                                       cp_map, pp_map, bf_map,
                                       img_prefix, pid, pagebreak=pagebreak)

        for name, data in src_bindata.items():
            fname_only = name.split("/", 1)[1]
            all_bindata[f"BinData/{img_prefix}{fname_only}"] = data

    # 재조립
    new_hdr = etree.tostring(header_tgt, xml_declaration=True,
                             encoding="UTF-8", standalone=True)
    new_sec = etree.tostring(root_tgt, xml_declaration=True,
                             encoding="UTF-8", standalone=True)

    existing_ids = set(re.findall(r'<opf:item id="([^"]+)"[^>]*BinData', base_hpf))
    new_items = ""
    for name in all_bindata:
        fname_only = name.split("/", 1)[1]
        img_id = fname_only.rsplit(".", 1)[0]
        if img_id not in existing_ids:
            ext = fname_only.rsplit(".", 1)[-1].lower()
            mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                        "png": "image/png", "bmp": "image/bmp", "gif": "image/gif"}
            new_items += (f'<opf:item id="{img_id}" href="BinData/{fname_only}" '
                          f'media-type="{mime_map.get(ext, "image/png")}" '
                          f'isEmbeded="1"/>')
    new_hpf = base_hpf.replace("</opf:manifest>", new_items + "</opf:manifest>")

    tmp = str(output) + ".tmp"
    with zipfile.ZipFile(str(base_path)) as zin:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            zi = zipfile.ZipInfo("mimetype")
            zi.compress_type = zipfile.ZIP_STORED
            zout.writestr(zi, zin.read("mimetype"))
            for item in zin.infolist():
                name = item.filename
                if name == "mimetype":
                    continue
                if name == "Contents/header.xml":
                    zout.writestr(item, new_hdr)
                elif name == "Contents/section0.xml":
                    zout.writestr(item, new_sec)
                elif name == "Contents/content.hpf":
                    zout.writestr(item, new_hpf.encode("utf-8"))
                elif name.startswith("BinData/"):
                    continue
                else:
                    zout.writestr(item, zin.read(name))
            for name, data in all_bindata.items():
                zout.writestr(name, data)
    shutil.move(tmp, str(output))

    print("fix_namespaces + validate")
    subprocess.run([sys.executable, str(SCRIPT_DIR / "fix_namespaces.py"),
                    str(output)], capture_output=True)
    r = subprocess.run([sys.executable, str(SCRIPT_DIR / "validate.py"),
                        str(output)],
                       capture_output=True, text=True, encoding="utf-8")
    print(r.stdout.strip())


# ==================== CLI ====================

def main():
    ap = argparse.ArgumentParser(
        description="HWPX N-파일 병합기 (첫 파일 기반 이어쓰기)"
    )
    ap.add_argument("files", nargs="+",
                    help="병합할 HWPX 파일 (2개 이상, 첫 파일이 고정 기반)")
    ap.add_argument("-o", "--output", required=True, help="출력 HWPX")
    ap.add_argument("--no-pagebreak", action="store_true",
                    help="파일 사이 페이지 넘김 생략")
    ap.add_argument("--img-prefix-tpl", default="s{idx}_",
                    help="이미지 접두어 템플릿 (기본: s{idx}_)")
    args = ap.parse_args()

    if len(args.files) < 2:
        ap.error("최소 2개 파일이 필요합니다")

    merge_hwpx(args.files, args.output,
               pagebreak=not args.no_pagebreak,
               img_prefix_tpl=args.img_prefix_tpl)


if __name__ == "__main__":
    main()
