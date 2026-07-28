#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""zip_replace_all.py

ZIP 레벨에서 .hwpx 패키지의 모든 XML 파트에 걸쳐 단순 텍스트 치환을 수행한다.

`HwpxModifier`/`HwpxFormFiller` 가 lxml 트리 기반인 반면, 이 스크립트는 표 셀까지
포함한 전역 string-level 치환에 특화돼 있다. 양식 문서에 흩어진 플레이스홀더
(`{학교명}`, `{기관명}` 등)를 빠르게 일괄 치환할 때 우선 고려.

원본: airmang/hwpx-skill (Apache-2.0). 이식 시 다음을 추가했다.
- 치환 후 section*.xml 에 `inject_dummy_linesegs()` 적용 → polaris-dvc strict
  검증의 JID 11004 ("paragraph has text but empty lineSegArray") 자동 회피
- `--no-ensure-linesegs` 로 더미 주입 비활성화 (원본 거동 그대로)

Usage:
  python3 scripts/zip_replace_all.py input.hwpx output.hwpx --replace "{A}=B"
  python3 scripts/zip_replace_all.py input.hwpx --inplace --backup --replace "{A}=B"
  python3 scripts/zip_replace_all.py input.hwpx output.hwpx --replace "{A}=B" --auto-fix-ns
"""

from __future__ import annotations

import argparse
import copy
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Mapping

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from fix_namespaces import fix_hwpx_namespaces  # noqa: E402
from hwpx_helpers import inject_dummy_linesegs  # noqa: E402


def _clone_zipinfo(info: zipfile.ZipInfo, *, force_stored: bool = False) -> zipfile.ZipInfo:
    cloned = copy.copy(info)
    if force_stored:
        cloned.compress_type = zipfile.ZIP_STORED
    return cloned


def _same_path(left: str | os.PathLike[str], right: str | os.PathLike[str]) -> bool:
    left_path = os.path.normcase(str(Path(left).resolve(strict=False)))
    right_path = os.path.normcase(str(Path(right).resolve(strict=False)))
    return left_path == right_path


def _make_temp_hwpx_path(directory: Path, prefix: str) -> str:
    fd, temp_path = tempfile.mkstemp(prefix=prefix, suffix=".hwpx", dir=directory)
    os.close(fd)
    return temp_path


def _is_section_xml(name: str) -> bool:
    """Contents/section\\d+.xml 형태인지 판정."""
    lower = name.lower().replace("\\", "/")
    return "/section" in lower and lower.endswith(".xml")


def parse_replace_args(values: list[str]) -> dict[str, str]:
    replacements: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"replacement must be OLD=NEW: {value!r}")
        old, new = value.split("=", 1)
        if not old:
            raise ValueError("replacement key must not be empty")
        replacements[old] = new
    if not replacements:
        raise ValueError("at least one replacement is required")
    return replacements


def warn_if_xml_like_keys(replacements: Mapping[str, str]) -> int:
    warnings = 0
    for old in replacements:
        if "<" in old or ">" in old or "</" in old:
            warnings += 1
            print(
                f"[WARN] replacement key looks like XML markup: {old!r}",
                file=sys.stderr,
            )
    return warnings


def zip_replace_all(
    in_hwpx: str | os.PathLike[str],
    out_hwpx: str | os.PathLike[str],
    replacements: Mapping[str, str],
    *,
    ensure_linesegs: bool = True,
) -> dict[str, int]:
    """HWPX 패키지의 모든 XML 파트에 string-level 치환 적용.

    Args:
        ensure_linesegs: True 면 section*.xml 에 한해 더미 lineSegArray 주입.

    Returns:
        통계 dict (parts/xml_parts/changed_xml/replacements/decode_failed/lineseg_injected)
    """

    stats = {
        "parts": 0,
        "xml_parts": 0,
        "changed_xml": 0,
        "replacements": 0,
        "decode_failed": 0,
        "lineseg_injected": 0,
    }

    # 입력=출력 경로면 ZipFile(out, "w")가 입력을 즉시 truncate 하므로 임시 파일 경유
    final_out: str | None = None
    if _same_path(in_hwpx, out_hwpx):
        final_out = str(out_hwpx)
        out_hwpx = _make_temp_hwpx_path(Path(final_out).parent, ".zip_replace_all-")

    with zipfile.ZipFile(in_hwpx, "r") as zin:
        with zipfile.ZipFile(out_hwpx, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                stats["parts"] += 1
                data = zin.read(info.filename)

                if info.filename.lower().endswith(".xml"):
                    stats["xml_parts"] += 1
                    try:
                        text = data.decode("utf-8")
                    except UnicodeDecodeError:
                        stats["decode_failed"] += 1
                        zout.writestr(
                            _clone_zipinfo(info, force_stored=info.filename == "mimetype"),
                            data,
                        )
                        continue

                    original_text = text
                    replaced_here = 0
                    for old, new in replacements.items():
                        count = text.count(old)
                        if count:
                            text = text.replace(old, new)
                            replaced_here += count

                    if text != original_text:
                        stats["changed_xml"] += 1
                        stats["replacements"] += replaced_here

                    if ensure_linesegs and _is_section_xml(info.filename):
                        text, injected = inject_dummy_linesegs(text)
                        if injected:
                            stats["lineseg_injected"] += injected

                    if text != original_text or (
                        ensure_linesegs and _is_section_xml(info.filename)
                    ):
                        data = text.encode("utf-8")

                zout.writestr(
                    _clone_zipinfo(info, force_stored=info.filename == "mimetype"),
                    data,
                )

    if final_out is not None:
        os.replace(out_hwpx, final_out)

    return stats


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Replace plain-text placeholders across XML parts in a .hwpx package. "
            "Use this for template-style global replacements, especially when table cells must be included."
        )
    )
    parser.add_argument("input_hwpx", help="Input .hwpx path")
    parser.add_argument(
        "output_hwpx",
        nargs="?",
        default=None,
        help="Output .hwpx path (omit when using --inplace)",
    )
    parser.add_argument(
        "--replace",
        nargs="+",
        required=True,
        metavar="OLD=NEW",
        help="One or more replacement pairs",
    )
    parser.add_argument(
        "--inplace",
        action="store_true",
        help="Write back to the input file using a temporary file internally",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="When overwriting the input file, create <input>.bak before replacing it",
    )
    parser.add_argument(
        "--auto-fix-ns",
        action="store_true",
        help="Run fix_hwpx_namespaces() after replacement (정규식 기반 ns 정리)",
    )
    parser.add_argument(
        "--no-ensure-linesegs",
        dest="ensure_linesegs",
        action="store_false",
        default=True,
        help="section*.xml 더미 lineSegArray 주입 비활성화 (airmang 원본 거동)",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)

    try:
        replacements = parse_replace_args(args.replace)
    except ValueError as exc:
        print(f"[ERR] {exc}", file=sys.stderr)
        return 2

    input_path = Path(args.input_hwpx).resolve()
    if not input_path.exists():
        print(f"[ERR] file not found: {input_path}", file=sys.stderr)
        return 2
    if not zipfile.is_zipfile(input_path):
        print(f"[ERR] not a ZIP file (invalid HWPX): {input_path}", file=sys.stderr)
        return 3

    if args.inplace and args.output_hwpx is not None:
        print("[ERR] do not pass output_hwpx with --inplace", file=sys.stderr)
        return 2
    if not args.inplace and args.output_hwpx is None:
        print("[ERR] output_hwpx is required unless --inplace is used", file=sys.stderr)
        return 2

    target_path = input_path if args.inplace else Path(args.output_hwpx).resolve()
    if not args.inplace:
        target_path.parent.mkdir(parents=True, exist_ok=True)
    needs_temp_output = args.inplace or _same_path(input_path, target_path)
    if needs_temp_output and not args.inplace:
        print(
            f"[WARN] output path matches input; using a temporary file: {target_path}",
            file=sys.stderr,
        )

    warn_if_xml_like_keys(replacements)

    temp_dir = input_path.parent
    replace_out = (
        Path(_make_temp_hwpx_path(temp_dir, "hwpx-replace-"))
        if needs_temp_output or args.auto_fix_ns
        else target_path
    )

    try:
        replace_stats = zip_replace_all(
            str(input_path),
            str(replace_out),
            replacements,
            ensure_linesegs=args.ensure_linesegs,
        )
    except Exception as exc:
        print(f"[ERR] replacement failed: {exc}", file=sys.stderr)
        if replace_out != target_path and replace_out.exists():
            replace_out.unlink(missing_ok=True)
        return 1

    final_path = target_path
    ns_applied = False

    if args.auto_fix_ns:
        # fix_hwpx_namespaces 는 in-place 함수 (단일 인자, 입력 파일을 직접 수정).
        try:
            fix_hwpx_namespaces(str(replace_out))
            ns_applied = True
        except Exception as exc:
            print(f"[ERR] namespace fix failed: {exc}", file=sys.stderr)
            replace_out.unlink(missing_ok=True)
            return 1
    produced_path = replace_out

    try:
        if produced_path != final_path:
            # temp → target 이동 (--inplace 든 --auto-fix-ns 든 동일 경로)
            if needs_temp_output and args.backup:
                backup_path = input_path.with_suffix(input_path.suffix + ".bak")
                shutil.copy2(input_path, backup_path)
                print(f"[OK] backup: {backup_path}")
            os.replace(produced_path, final_path)
        elif args.backup:
            print("[WARN] --backup is ignored when output does not overwrite input", file=sys.stderr)
    finally:
        if produced_path != final_path and Path(produced_path).exists():
            Path(produced_path).unlink(missing_ok=True)

    print(f"[OK] wrote: {final_path}")
    print(
        "[STATS] "
        f"parts={replace_stats['parts']} xml={replace_stats['xml_parts']} "
        f"changed_xml={replace_stats['changed_xml']} replacements={replace_stats['replacements']} "
        f"lineseg_injected={replace_stats['lineseg_injected']} "
        f"decode_failed={replace_stats['decode_failed']}"
    )
    if ns_applied:
        print("[NS] fix_hwpx_namespaces applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
