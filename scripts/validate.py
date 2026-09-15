#!/usr/bin/env python3
"""Validate the structural integrity of an HWPX file.

Checks:
  - Valid ZIP archive
  - Required files present (mimetype, content.hpf, header.xml, section0.xml)
  - mimetype content is correct
  - mimetype is the first ZIP entry and stored without compression
  - All XML files are well-formed

Usage:
    python validate.py document.hwpx
"""

import argparse
import sys
from pathlib import Path
from zipfile import ZIP_STORED, BadZipFile, ZipFile

from lxml import etree

REQUIRED_FILES = [
    "mimetype",
    "Contents/content.hpf",
    "Contents/header.xml",
    "Contents/section0.xml",
]

EXPECTED_MIMETYPE = "application/hwp+zip"


def validate(hwpx_path: str) -> list[str]:
    """Validate HWPX file and return a list of error messages (empty = valid)."""

    errors: list[str] = []
    path = Path(hwpx_path)

    if not path.is_file():
        return [f"File not found: {hwpx_path}"]

    # Check valid ZIP
    try:
        zf = ZipFile(hwpx_path, "r")
    except BadZipFile:
        return [f"Not a valid ZIP archive: {hwpx_path}"]

    with zf:
        names = zf.namelist()

        # Check required files
        for required in REQUIRED_FILES:
            if required not in names:
                errors.append(f"Missing required file: {required}")

        # Check mimetype content
        if "mimetype" in names:
            mimetype_content = zf.read("mimetype").decode("utf-8").strip()
            if mimetype_content != EXPECTED_MIMETYPE:
                errors.append(
                    f"Invalid mimetype: expected '{EXPECTED_MIMETYPE}', "
                    f"got '{mimetype_content}'"
                )

            # Check mimetype is first entry
            if names[0] != "mimetype":
                errors.append(
                    f"mimetype is not the first ZIP entry (found at index "
                    f"{names.index('mimetype')})"
                )

            # Check mimetype is stored without compression
            info = zf.getinfo("mimetype")
            if info.compress_type != ZIP_STORED:
                errors.append(
                    f"mimetype should use ZIP_STORED (0), "
                    f"got compress_type={info.compress_type}"
                )

        # Check XML well-formedness
        for name in names:
            if name.endswith(".xml") or name.endswith(".hpf"):
                try:
                    data = zf.read(name)
                    etree.fromstring(data)
                except etree.XMLSyntaxError as e:
                    errors.append(f"Malformed XML in {name}: {e}")

    # 쪽 크기 상식 검사 — 2026-09-15 실측: 코덱스가 본문 글자를 바꾸려고 XML 전체에 문자열 치환을 걸어
    # pagePr height 가 84186 → 8, 여백 1417 → 14 로 바뀐 파일이 XML 유효성은 통과하고 한글은 쪽을 넘기다 멈췄다.
    if not errors:
        try:
            with ZipFile(hwpx_path, "r") as zf:
                for name in zf.namelist():
                    if not (name.startswith("Contents/section") and name.endswith(".xml")):
                        continue
                    root = etree.fromstring(zf.read(name))
                    for el in root.iter():
                        if el.tag.split("}")[-1] != "pagePr":
                            continue
                        w, h = int(el.get("width", 0)), int(el.get("height", 0))
                        if not (10000 <= w <= 300000 and 10000 <= h <= 300000):
                            errors.append(
                                f"{name}: pagePr 크기가 비정상 (width={w}, height={h} HWPUNIT). "
                                "A4 는 59528×84186 — 문자열 치환이 속성값을 건드렸을 가능성")
        except Exception as e:
            errors.append(f"쪽 크기 검사 실패: {e}")

    # 표 격자 정합성 — XML 이 유효해도 cellAddr 가 겹치거나 비면 한컴이 문서를 열다 멈춘다.
    # 2026-09-15 실측: 코덱스가 행을 복제하며 rowAddr 를 안 고친 hwpx 가 이 검사를 통과해 「구조 정상」으로 나갔고
    # 한글이 그 파일을 열다가 응답 없음이 됐다. 검사 본체는 verify_hwpx.check_table_grid 를 쓴다.
    if not errors:
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from verify_hwpx import check_table_grid
            grid = check_table_grid(hwpx_path)
            errors.extend(grid.get("errors", []))
        except Exception as e:  # 검사 자체가 죽어도 유효성 결과는 낸다
            errors.append(f"표 격자 검사 실패: {e}")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the structural integrity of an HWPX file"
    )
    parser.add_argument("input", help="Path to .hwpx file")
    args = parser.parse_args()

    errors = validate(args.input)

    if errors:
        print(f"INVALID: {args.input}", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"VALID: {args.input}")
        print(f"  All structural checks passed.")


if __name__ == "__main__":
    main()
