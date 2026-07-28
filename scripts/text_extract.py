#!/usr/bin/env python3
"""Extract text from an HWPX document.

Wraps python-hwpx's TextExtractor for convenient CLI use.

Usage:
    python text_extract.py document.hwpx
    python text_extract.py document.hwpx --format markdown
    python text_extract.py document.hwpx --include-tables
"""

import argparse
import sys
from pathlib import Path

from hwpx import TextExtractor


def extract_plain(hwpx_path: str, *, include_tables: bool = False) -> str:
    """Extract plain text from HWPX file.

    include_nested와 object_behavior="nested"를 함께 주면 표 셀을 두 경로가
    각각 방문해 셀 텍스트가 그대로 두 번 나온다. 중첩 문단 순회(include_nested)
    하나만 켜고 객체 펼치기는 끈다.
    """

    with TextExtractor(hwpx_path) as ext:
        return ext.extract_text(
            include_nested=include_tables,
            object_behavior="skip",
            skip_empty=True,
        )


def extract_markdown(hwpx_path: str) -> str:
    """Extract text as Markdown with section separators."""

    lines: list[str] = []

    with TextExtractor(hwpx_path) as ext:
        for section in ext.iter_sections():
            if lines:
                lines.append("")
                lines.append("---")
                lines.append("")

            for para in ext.iter_paragraphs(section, include_nested=True):
                # include_nested가 이미 표 셀 문단을 돌므로 객체를 다시 펼치면 중복된다
                text = para.text(object_behavior="skip")
                if text.strip():
                    if para.is_nested:
                        # Table cell or nested content - indent
                        lines.append(f"  {text}")
                    else:
                        lines.append(text)

    return "\n".join(lines)


def _has_table(hwpx_path: str) -> bool:
    """섹션 XML에 표가 있는지 확인한다(표준 라이브러리만 사용)."""
    import zipfile

    try:
        with zipfile.ZipFile(hwpx_path) as zf:
            for name in zf.namelist():
                if name.startswith("Contents/section") and name.endswith(".xml"):
                    if b"<hp:tbl" in zf.read(name):
                        return True
    except Exception:
        pass
    return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract text from an HWPX document"
    )
    parser.add_argument("input", help="Path to .hwpx file")
    parser.add_argument(
        "--format", "-f",
        choices=["plain", "markdown"],
        default="plain",
        help="Output format (default: plain)",
    )
    parser.add_argument(
        "--include-tables",
        action="store_true",
        help="Include text from tables and nested objects (plain mode)",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: stdout)",
    )
    args = parser.parse_args()

    if not Path(args.input).is_file():
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    if args.format == "markdown":
        result = extract_markdown(args.input)
    else:
        # 표가 있는데 --include-tables 없이 뽑으면 셀 내용이 통째로 빠진다.
        # 원고와 실물을 대조하는 용도(Critical Rule 34)에서는 치명적이므로 알린다.
        if not args.include_tables and _has_table(args.input):
            print(
                "NOTE: 이 문서에는 표가 있다. --include-tables 없이 뽑으면 "
                "셀 내용이 결과에서 빠진다.",
                file=sys.stderr,
            )
        result = extract_plain(args.input, include_tables=args.include_tables)

    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        print(f"Extracted to: {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
