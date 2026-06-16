#!/usr/bin/env python3
"""
HWPX 문서 검수 도구 (서브에이전트용)

생성된 HWPX 문서를 원본과 비교하여 구조 보존 여부, XML 유효성,
텍스트 치환 결과를 종합 검증한다.

서브에이전트가 문서 생성 후 품질 검증 단계에서 사용한다.

사용법:
  # 원본과 비교 검수
  python verify_hwpx.py --source original.hwpx --result output.hwpx

  # 단독 검수 (원본 없이)
  python verify_hwpx.py --result output.hwpx

  # JSON 리포트 출력
  python verify_hwpx.py --source original.hwpx --result output.hwpx --json report.json
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

# rhwp (edwardkim/rhwp, src/parser/hwpx/reader.rs:19-26) 기반 zip bomb 상한
ZIP_MAX_XML_SIZE = 32 * 1024 * 1024       # 32 MB — XML/HPF 엔트리
ZIP_MAX_BINDATA_SIZE = 64 * 1024 * 1024   # 64 MB — BinData/* 이미지/폰트

# polaris-dvc (PolarisOffice/polaris_dvc) — 외부 바이너리, 선택적 의존성
_SKILL_BIN = Path(__file__).parent.parent / "bin" / "polaris-dvc.exe"


def _find_polaris_dvc():
    """polaris-dvc 바이너리 위치 탐색. 없으면 None."""
    if _SKILL_BIN.exists():
        return str(_SKILL_BIN)
    return shutil.which("polaris-dvc")


def _check_zip_bomb(zf, names):
    """zip bomb 방어: 엔트리별 해제 크기 상한 검증.

    위반 목록(빈 리스트 = 안전)을 반환한다.
    """
    violations = []
    for name in names:
        try:
            info = zf.getinfo(name)
        except KeyError:
            continue
        limit = ZIP_MAX_BINDATA_SIZE if name.startswith("BinData/") else ZIP_MAX_XML_SIZE
        if info.file_size > limit:
            violations.append({"entry": name, "size": info.file_size, "limit": limit})
    return violations


def _count_structure(hwpx_path):
    """HWPX 구조 요소를 카운트한다."""
    result = {"path": hwpx_path}

    with zipfile.ZipFile(hwpx_path, "r") as zf:
        names = zf.namelist()
        result["zip_entries"] = len(names)
        result["bindata"] = len([n for n in names if n.startswith("BinData/")])

        # zip bomb 상한 체크 (rhwp 기반)
        zb = _check_zip_bomb(zf, names)
        result["zip_bomb_safe"] = not zb
        if zb:
            result["zip_bomb_violations"] = zb

        # mimetype 검사
        result["mimetype_first"] = names[0] == "mimetype" if names else False
        if "mimetype" in names:
            info = zf.getinfo("mimetype")
            result["mimetype_stored"] = info.compress_type == zipfile.ZIP_STORED
        else:
            result["mimetype_stored"] = False

        # 필수 파일
        required = ["mimetype", "Contents/content.hpf",
                     "Contents/header.xml", "Contents/section0.xml"]
        result["required_files"] = {r: r in names for r in required}

        # section0.xml 분석
        if "Contents/section0.xml" in names:
            sec = zf.read("Contents/section0.xml").decode("utf-8")
            result["section_size"] = len(sec)
            result["paragraphs"] = len(re.findall(r"<hp:p ", sec))
            result["runs"] = len(re.findall(r"<hp:run ", sec))
            result["tables"] = len(re.findall(r"<hp:tbl ", sec))
            result["images"] = len(re.findall(r"<hp:pic ", sec))

        # XML 파싱 검사
        xml_ok, xml_fail, xml_errors = 0, 0, []
        try:
            from lxml import etree
            for name in names:
                if name.endswith(".xml") or name.endswith(".hpf"):
                    try:
                        etree.fromstring(zf.read(name))
                        xml_ok += 1
                    except etree.XMLSyntaxError as e:
                        xml_fail += 1
                        xml_errors.append(f"{name}: {e}")
        except ImportError:
            # lxml 없으면 기본 XML 파서 사용
            import xml.etree.ElementTree as ET
            for name in names:
                if name.endswith(".xml") or name.endswith(".hpf"):
                    try:
                        ET.fromstring(zf.read(name))
                        xml_ok += 1
                    except ET.ParseError as e:
                        xml_fail += 1
                        xml_errors.append(f"{name}: {e}")

        result["xml_valid"] = xml_ok
        result["xml_invalid"] = xml_fail
        result["xml_errors"] = xml_errors

    return result


def _run_polaris_dvc(hwpx_path, spec_path=None):
    """polaris-dvc 실행 → JID 위반 목록 반환.

    바이너리 미설치·실행 실패 시 None.
    spec_path 미제공 시 규칙 적합성 축은 비활성, 구조/컨테이너 위반만 검출.
    """
    binary = _find_polaris_dvc()
    if not binary:
        return None

    cmd = [binary]
    if spec_path:
        cmd += ["-t", spec_path]
    cmd.append(str(hwpx_path))

    try:
        proc = subprocess.run(
            cmd, capture_output=True, timeout=30,
            encoding="utf-8", errors="replace",
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        return {"error": f"polaris-dvc 실행 실패: {e}"}

    # exit code: 0=깨끗, 1=위반 검출, 2=사용법 오류, 3=입력 오류
    if proc.returncode in (0, 1):
        try:
            violations = json.loads(proc.stdout) if proc.stdout.strip() else []
        except json.JSONDecodeError as e:
            return {"error": f"polaris-dvc JSON 파싱 실패: {e}"}
        return {"violations": violations, "binary": binary}

    return {"error": f"polaris-dvc exit {proc.returncode}: {proc.stderr.strip()[:200]}"}


def _extract_texts(hwpx_path):
    """텍스트 추출 (간소화 버전)."""
    texts = []
    with zipfile.ZipFile(hwpx_path, "r") as zf:
        for name in zf.namelist():
            if name.startswith("Contents/") and name.endswith(".xml"):
                data = zf.read(name).decode("utf-8")
                for m in re.finditer(r"<hp:t>(.*?)</hp:t>", data, re.DOTALL):
                    clean = re.sub(r"<[^>]+>", "", m.group(1)).strip()
                    if clean:
                        texts.append(clean)
    return texts


# ─── 글자 테두리 버그 탐지·제거 (jkf87/hwpx-skill 차용, 2026-06-16) ───
# hwp2hwpx 변환기·일부 LLM 산출물이 charPr 다수에 동일 SOLID 테두리 borderFill을
# 참조시켜 "모든 글자에 네모 테두리"가 보이는 버그. 표 셀(tc) borderFill은
# section에 있어 건드리지 않으므로 표 테두리는 보존된다. (내 스킬은 생성 시
# Rule 24로 예방하나, convert_hwp.py·외부 양식 편집 경로는 사후 보정이 필요.)
_CHARPR_OPEN_RE = re.compile(r"<(?:\w+:)?charPr\b[^>]*?>")
_BORDERREF_RE = re.compile(r'\s*borderFillIDRef="\d+"')
_CHARPR_REF_RE = re.compile(r'<(?:\w+:)?charPr\b[^>]*?borderFillIDRef="(\d+)"')
_BORDER_SOLID_RE = re.compile(
    r'(?:left|right|top|bottom)Border type="'
    r'(?:SOLID|DASH|DOT|THICK|DOUBLE|WAVE)"')


def _borderfill_is_solid(header_xml, bid):
    """header.xml에서 borderFill id=bid가 실제 테두리선을 가지는지."""
    m = re.search(rf'<(?:\w+:)?borderFill\b[^>]*\bid="{bid}"', header_xml)
    if not m:
        return False
    close = re.search(r"</(?:\w+:)?borderFill>", header_xml[m.start():])
    block = (header_xml[m.start():m.start() + close.end()]
             if close else header_xml[m.start():m.start() + 600])
    return bool(_BORDER_SOLID_RE.search(block))


def detect_char_border_bug(hwpx_path):
    """글자모양(charPr)에 테두리가 박힌 변환기/LLM 버그인지 탐지.

    charPr의 절반 이상이 '실제 테두리선이 있는' borderFill을 참조할 때만
    버그로 판정한다(의도적 글자 테두리는 일부 charPr만 참조).

    Returns: {"bug": bool, "bordered_charpr": int, "total_charpr": int}
    """
    with zipfile.ZipFile(hwpx_path) as zf:
        names = [n for n in zf.namelist() if n.endswith("header.xml")]
        if not names:
            return {"bug": False, "bordered_charpr": 0, "total_charpr": 0}
        h = zf.read(names[0]).decode("utf-8")

    total = len(re.findall(r"<(?:\w+:)?charPr\b", h))
    solid_cache, bordered = {}, 0
    for bid in _CHARPR_REF_RE.findall(h):
        if bid not in solid_cache:
            solid_cache[bid] = _borderfill_is_solid(h, bid)
        if solid_cache[bid]:
            bordered += 1
    bug = total > 0 and bordered >= max(2, total * 0.5)
    return {"bug": bug, "bordered_charpr": bordered, "total_charpr": total}


def strip_char_borders(hwpx_path, output_path=None):
    """charPr에 박힌 글자 테두리 참조(borderFillIDRef)를 제거.

    header.xml의 charPr만 손대므로 표 셀(section의 tc) 테두리는 보존된다.
    idempotent — 제거할 게 없으면 원본을 그대로 두고 0을 반환한다.

    Returns: 제거한 참조 수.
    """
    src = Path(hwpx_path)
    dst = Path(output_path) if output_path else src

    with zipfile.ZipFile(src, "r") as zf:
        headers = {n: zf.read(n).decode("utf-8")
                    for n in zf.namelist() if n.endswith("header.xml")}

    patched, total = {}, 0
    for name, h in headers.items():
        h2 = _CHARPR_OPEN_RE.sub(
            lambda m: _BORDERREF_RE.sub("", m.group(0)), h)
        removed = h.count("borderFillIDRef") - h2.count("borderFillIDRef")
        if removed:
            patched[name] = h2.encode("utf-8")
            total += removed

    if not patched:
        if dst != src:
            shutil.copyfile(src, dst)
        return 0

    tmp = str(dst) + ".tmp"
    with zipfile.ZipFile(src, "r") as zin:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = patched.get(item.filename, zin.read(item.filename))
                if item.filename == "mimetype":
                    zout.writestr(item, data, compress_type=zipfile.ZIP_STORED)
                else:
                    zout.writestr(item, data)
    os.replace(tmp, str(dst))
    return total


# ─── secPr 완전성 점검 (jkf87/hwpx-skill check_openable 차용, 2026-06-16) ─
# XML 유효성(validate.py)·구조 보존 비교로는 못 잡는, secPr 자식요소
# (pagePr/margin) 누락 및 LLM이 손수 만든 가짜 secPr를 검출 → 한컴 '손상된
# 문서' 복구 대화상자 사고 방지.
_SECPR_REQUIRED = ("pagePr", "margin")
_SECPR_BOGUS_ATTRS = ("pageWidth", "pageHeight", "leftMargin",
                       "rightMargin", "topMargin")


def check_secpr_openable(hwpx_path):
    """첫 섹션 secPr의 완전성 점검 — 한컴 열림 가능성 정적 검사.

    Returns: {"errors": [...], "warnings": [...]}
    """
    errors, warnings = [], []
    try:
        from lxml import etree
    except ImportError:
        return {"errors": [], "warnings": ["lxml 미설치 — secPr 점검 건너뜀"]}

    with zipfile.ZipFile(hwpx_path, "r") as zf:
        secs = sorted(n for n in zf.namelist()
                       if n.startswith("Contents/section") and n.endswith(".xml"))
        if not secs:
            return {"errors": ["섹션 파일 없음"], "warnings": []}
        data = zf.read(secs[0])

    try:
        root = etree.fromstring(data)
    except etree.XMLSyntaxError as e:
        return {"errors": [f"section0.xml 파싱 실패: {e}"], "warnings": []}

    hp = "http://www.hancom.co.kr/hwpml/2011/paragraph"
    secprs = root.findall(f".//{{{hp}}}secPr")
    if not secprs:
        errors.append("첫 섹션에 <hp:secPr>가 없음 — 한컴이 열지 못함")
        return {"errors": errors, "warnings": warnings}

    secpr = secprs[0]
    child_tags = {etree.QName(c).localname for c in secpr.iter() if c is not secpr}
    for req in _SECPR_REQUIRED:
        if req not in child_tags:
            label = "용지 크기" if req == "pagePr" else "여백"
            errors.append(
                f"secPr에 <hp:{req}> 없음 — {label} 미정의로 한컴 열기 실패")

    bogus = [a for a in _SECPR_BOGUS_ATTRS if a in secpr.attrib]
    if bogus:
        errors.append(
            f"secPr에 비표준 속성 {bogus} — LLM이 손수 작성한 가짜 secPr로 보임. "
            "정상 HWPX의 secPr(pagePr/margin 자식 요소)로 교체 필요")

    return {"errors": errors, "warnings": warnings}


def verify(source_path=None, result_path=None, json_output=None,
            strict=False, spec_path=None, fix_borders=False):
    """HWPX 검수를 실행한다.

    Args:
        source_path: 원본 .hwpx (비교 검수 시)
        result_path: 결과 .hwpx (필수)
        json_output: JSON 리포트 경로 (선택)
        strict: True 면 polaris-dvc로 JID 위반까지 검출
        spec_path: polaris-dvc 규칙 spec JSON (--strict 와 함께 사용, 선택)
        fix_borders: True 면 검사 전 글자 테두리 버그를 자동 제거

    Returns:
        dict: 검수 결과
    """
    report = {"status": "UNKNOWN", "issues": [], "warnings": []}

    if not result_path or not os.path.exists(result_path):
        report["status"] = "FAIL"
        report["issues"].append(f"결과 파일 없음: {result_path}")
        return report

    # 0. (선택) 글자 테두리 버그 자동 제거 — 검사 전에 보정
    if fix_borders:
        removed = strip_char_borders(result_path)
        report["actions"] = [f"글자 테두리 borderFillIDRef {removed}개 제거"]
        print(f"🔧 글자 테두리 borderFillIDRef {removed}개 제거됨"
              if removed else "🔧 제거할 글자 테두리 없음")

    # 1. 결과 파일 구조 분석
    result_info = _count_structure(result_path)
    report["result"] = result_info

    # 기본 검증
    if not result_info.get("mimetype_first"):
        report["issues"].append("mimetype이 ZIP 첫 엔트리가 아님")
    if not result_info.get("mimetype_stored"):
        report["issues"].append("mimetype이 ZIP_STORED가 아님")
    for fname, exists in result_info.get("required_files", {}).items():
        if not exists:
            report["issues"].append(f"필수 파일 누락: {fname}")
    if result_info.get("xml_invalid", 0) > 0:
        report["issues"].append(
            f"XML 파싱 실패 {result_info['xml_invalid']}개: "
            + "; ".join(result_info.get("xml_errors", []))
        )
    # zip bomb 상한 위반
    for v in result_info.get("zip_bomb_violations", []):
        report["issues"].append(
            f"엔트리 크기 상한 초과 ({v['entry']}: {v['size']} > {v['limit']}) — zip bomb 가능성"
        )

    # 1.3. secPr 완전성 (한컴 열림 가능성) — '손상된 문서' 사고 방지
    secpr_check = check_secpr_openable(result_path)
    report["issues"].extend(secpr_check["errors"])
    report["warnings"].extend(secpr_check["warnings"])

    # 1.4. 글자 테두리 버그 (모든 글자에 네모 테두리)
    cb = detect_char_border_bug(result_path)
    result_info["char_border_bug"] = cb["bug"]
    if cb["bug"]:
        report["warnings"].append(
            f"글자 테두리 버그 ({cb['bordered_charpr']}/{cb['total_charpr']} "
            "charPr이 테두리 borderFill 참조) — 모든 글자에 네모 테두리. "
            "`verify_hwpx.py --result <file> --fix-borders`로 제거"
        )

    # 1.5. polaris-dvc strict 검증 (선택적)
    if strict:
        polaris = _run_polaris_dvc(result_path, spec_path)
        if polaris is None:
            report["warnings"].append(
                "polaris-dvc 미설치 — strict 검증 건너뜀 "
                f"(설치 위치: {_SKILL_BIN} 또는 PATH)"
            )
        elif "error" in polaris:
            report["warnings"].append(f"polaris-dvc: {polaris['error']}")
        else:
            from collections import Counter
            v = polaris["violations"]
            jid_counts = Counter(item["ErrorCode"] for item in v)
            report["polaris"] = {
                "binary": polaris["binary"],
                "total_violations": len(v),
                "by_jid": dict(jid_counts.most_common()),
                "samples": v[:5],  # 상위 5개 샘플만
            }
            if v:
                top = ", ".join(f"JID {j}({c})" for j, c in jid_counts.most_common(3))
                report["issues"].append(
                    f"polaris-dvc 위반 {len(v)}건: {top}"
                )

    # 2. 원본과 비교 (제공된 경우)
    if source_path and os.path.exists(source_path):
        source_info = _count_structure(source_path)
        report["source"] = source_info

        comparison = {}

        # 구조 보존 비교
        for key in ["zip_entries", "bindata", "paragraphs", "runs",
                     "tables", "images"]:
            src_val = source_info.get(key, 0)
            res_val = result_info.get(key, 0)
            diff = res_val - src_val
            comparison[key] = {
                "source": src_val, "result": res_val, "diff": diff
            }
            if key in ("runs", "tables", "images") and diff < 0:
                report["issues"].append(
                    f"{key} 감소: {src_val} → {res_val} (차이: {diff})"
                )
            elif key in ("runs",) and diff < 0:
                report["warnings"].append(
                    f"{key} 변경: {src_val} → {res_val}"
                )

        # section 크기 비율
        src_size = source_info.get("section_size", 1)
        res_size = result_info.get("section_size", 0)
        ratio = res_size / src_size * 100 if src_size > 0 else 0
        comparison["section_size_ratio"] = round(ratio, 1)

        if ratio < 50:
            report["issues"].append(
                f"section0.xml 크기 비율 {ratio:.1f}% — 구조 대량 손실 의심"
            )
        elif ratio < 90:
            report["warnings"].append(
                f"section0.xml 크기 비율 {ratio:.1f}% — 일부 구조 변경 가능"
            )

        report["comparison"] = comparison

    # 3. 최종 판정
    if report["issues"]:
        report["status"] = "FAIL"
    elif report["warnings"]:
        report["status"] = "WARN"
    else:
        report["status"] = "PASS"

    # 출력
    _print_report(report)

    if json_output:
        with open(json_output, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\nJSON 리포트: {json_output}")

    return report


def _print_report(report):
    """검수 결과를 콘솔에 출력한다."""
    status_icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(
        report["status"], "❓"
    )
    print(f"\n{'='*60}")
    print(f"  HWPX 검수 결과: {status_icon} {report['status']}")
    print(f"{'='*60}")

    # 결과 파일 정보
    if "result" in report:
        r = report["result"]
        print(f"\n[결과 파일]")
        print(f"  ZIP엔트리: {r.get('zip_entries', '?')}개, "
              f"BinData: {r.get('bindata', '?')}개")
        print(f"  문단: {r.get('paragraphs', '?')}, "
              f"런: {r.get('runs', '?')}, "
              f"테이블: {r.get('tables', '?')}, "
              f"이미지: {r.get('images', '?')}")
        print(f"  XML: 유효 {r.get('xml_valid', 0)}개, "
              f"오류 {r.get('xml_invalid', 0)}개")

    # 비교 결과
    if "comparison" in report:
        c = report["comparison"]
        print(f"\n[원본 대비 비교]")
        for key in ["paragraphs", "runs", "tables", "images", "bindata"]:
            if key in c:
                d = c[key]
                diff_str = f"+{d['diff']}" if d["diff"] > 0 else str(d["diff"])
                icon = "✅" if d["diff"] == 0 else ("⚠️" if d["diff"] > 0 else "❌")
                print(f"  {icon} {key}: {d['source']} → {d['result']} ({diff_str})")
        if "section_size_ratio" in c:
            ratio = c["section_size_ratio"]
            icon = "✅" if ratio >= 90 else ("⚠️" if ratio >= 50 else "❌")
            print(f"  {icon} section 크기 비율: {ratio}%")

    # polaris-dvc 결과
    if "polaris" in report:
        p = report["polaris"]
        print(f"\n[polaris-dvc strict 검증]")
        print(f"  총 위반: {p['total_violations']}건")
        if p["by_jid"]:
            for jid, count in list(p["by_jid"].items())[:5]:
                print(f"    JID {jid}: {count}건")

    # 이슈
    if report["issues"]:
        print(f"\n[이슈 ({len(report['issues'])}개)]")
        for issue in report["issues"]:
            print(f"  ❌ {issue}")

    if report["warnings"]:
        print(f"\n[경고 ({len(report['warnings'])}개)]")
        for warn in report["warnings"]:
            print(f"  ⚠️ {warn}")

    if not report["issues"] and not report["warnings"]:
        print(f"\n  모든 검사 통과!")


def main():
    parser = argparse.ArgumentParser(
        description="HWPX 문서 검수 도구 (서브에이전트용)",
    )
    parser.add_argument("--source", help="원본 HWPX 파일 (비교 검수)")
    parser.add_argument("--result", required=True, help="검수 대상 HWPX 파일")
    parser.add_argument("--json", help="JSON 리포트 출력 경로")
    parser.add_argument("--strict", action="store_true",
                          help="polaris-dvc로 JID 위반 검출 (선택)")
    parser.add_argument("--spec", help="polaris-dvc 규칙 spec JSON 경로 (선택)")
    parser.add_argument("--fix-borders", action="store_true",
                          help="검사 전 글자 테두리 버그를 자동 제거 (대상 파일 직접 수정)")

    args = parser.parse_args()
    report = verify(args.source, args.result, args.json,
                     strict=args.strict, spec_path=args.spec,
                     fix_borders=args.fix_borders)

    sys.exit(0 if report["status"] in ("PASS", "WARN") else 1)


if __name__ == "__main__":
    main()
