#!/usr/bin/env python3
"""HWPX 자동 첨삭 메모 batch 삽입 CLI.

`HwpxDocument.add_memo_with_anchor(...)` 를 활용해서 학생 작품·보고서에
첨삭 메모를 일괄 추가한다.

JSON 입력 스키마 (배열):
[
  {
    "section": 0,                     # 섹션 인덱스 (기본 0)
    "paragraph": 3,                   # 문단 인덱스 (필수, 0-based)
    "text": "여기 보충 필요",          # 메모 본문 (필수)
    "author": "임세범"                 # 메모 작성자 (선택)
  },
  ...
]

또는 paragraph_text 매칭으로(그 글이 든 첫 문단, 표 칸 안 포함):
[
  {"paragraph_text": "학습 목표:", "text": "구체적 행동동사 사용 권장", "author": "교사"}
]

메모는 한/글이 읽는 모양으로 저장한다(memos_to_hancom_shape — python-hwpx 가 쓴 그대로는
한/글에서 본문 대신 메모 id 숫자가 보인다).

요구사항: python-hwpx >= 2.6.

Usage:
  python3 add_review_memo.py student.hwpx graded.hwpx --memos memos.json
  echo '[{"paragraph": 0, "text": "잘 썼어요"}]' | \\
      python3 add_review_memo.py student.hwpx graded.hwpx --memos -
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from hwpx_helpers import inject_dummy_linesegs  # noqa: E402

# 한/글이 메모 필드의 fieldid 로 쓰는 값(HWP5 컨트롤 id '%%me')
MEMO_CTRL_ID = 623209829

# python-hwpx 가 쓴 메모 필드: subList id 가 "memo-field-<메모 id>" 이고 그 안에는 메모 id 만 글로 들어 있다
_PY_MEMO_FIELD_RE = re.compile(
    r'<hp:fieldBegin\b(?P<attrs>[^>]*\btype="MEMO"[^>]*)>\s*'
    r"<hp:parameters\b[^>]*>(?P<params>(?:(?!</hp:parameters>).)*)</hp:parameters>\s*"
    r'<hp:subList\b[^>]*\bid="memo-field-[^"]*"[^>]*>(?:(?!</hp:subList>).)*</hp:subList>\s*'
    r"</hp:fieldBegin>",
    re.S,
)
# 작성자에 남길 글자. 한/글은 작성자를 Command 의 작성자 칸에서 읽는데(Author 매개변수는 거기서 다시 만든다),
# 그 칸에 `:` `;` `\` `?` `|` 가 있으면 메모 매개변수가 통째로 깨지고 `/` 는 그 앞에서 이름이 잘린다
# (한/글 2024 변형 시험 2026-10-06). 글자, 숫자, 공백과 아래 기호는 그대로 남는 것을 확인했다.
_SAFE_AUTHOR_RE = re.compile(r"[^\w .,()&='\"!@*%+~-]")
_MEMOGROUP_RE = re.compile(r"<hp:memogroup\b[^>]*>.*?</hp:memogroup>", re.S)
_MEMO_RE = re.compile(r'<hp:memo\b[^>]*\bid="([^"]*)"[^>]*>(.*?)</hp:memo>', re.S)


def _memo_param(params: str, name: str) -> str:
    m = re.search(rf'<hp:\w+Param name="{name}"\s*>([^<]*)</hp:\w+Param>', params)
    return m.group(1) if m else ""


def _memo_style(header_xml: str) -> tuple[str, str, str]:
    """「메모」 스타일의 (스타일 id, 문단 모양 id, 글자 모양 id). 없으면 바탕글(0, 0, 0)."""
    for tag in re.findall(r"<hh:style\b[^>]*>", header_xml):
        attrs = dict(re.findall(r'(\w+)="([^"]*)"', tag))
        if attrs.get("name") == "메모" or attrs.get("engName") == "Memo":
            return (
                attrs.get("id", "0"),
                attrs.get("paraPrIDRef", "0"),
                attrs.get("charPrIDRef", "0"),
            )
    return "0", "0", "0"


def memos_to_hancom_shape(
    sections: dict[str, str], header_xml: str
) -> tuple[dict[str, str], int]:
    """python-hwpx 가 쓴 메모를 한/글이 읽는 모양으로 바꾼다. 반환: (구역 XML, 바꾼 메모 수).

    python-hwpx `add_memo_with_anchor` 는 메모 본문을 구역 끝 `<hp:memogroup>` 에 두고, 메모 필드의
    subList 에는 메모 id 만 글로 적는다. 한/글 2024 는 그 묶음을 읽지 않아 메모 풍선에 **id 숫자**가
    보이고, 다시 저장하면 본문이 사라진다(2026-10-06 실측). 한/글이 스스로 쓰는 모양은 이렇다:

    - 본문은 `fieldBegin type="MEMO"` 안 subList 의 문단(줄마다 한 문단)
    - `zorder` = 메모 번호(`Number`). 다르면 한/글이 메모의 끝 표식(fieldEnd)을 버린다
    - `fieldid` = 623209829, `Command` = `MEMO/65535/<번호>/<FILETIME 하위>/<상위>/<작성자>/\\;;`
    - `CreateDateTime` 은 지역 시각에 Z 를 붙인 꼴

    번호는 문서에 이미 있는 한/글 메모 다음부터 문서 순서로 매긴다(python-hwpx 는 모두 1 을 준다).
    """
    style_id, para_pr, char_pr = _memo_style(header_xml)
    whole = "".join(sections.values())
    used_ids = {int(v) for v in re.findall(r'<hp:fieldBegin\b[^>]*\bid="(\d+)"', whole)}
    number = max(
        (
            int(v)
            for v in re.findall(
                r'<hp:fieldBegin\b[^>]*\btype="MEMO"[^>]*\bzorder="(\d+)"', whole
            )
        ),
        default=0,
    )
    converted = 0
    out: dict[str, str] = {}
    for name, xml in sections.items():
        bodies = {
            memo_id: "\n".join(
                "".join(re.findall(r"<hp:t\b[^>]*>([^<]*)</hp:t>", para))
                for para in re.findall(r"<hp:p\b[^>]*>.*?</hp:p>", inner, re.S)
            )
            for group in _MEMOGROUP_RE.findall(xml)
            for memo_id, inner in _MEMO_RE.findall(group)
        }
        done: set[str] = set()
        end_ids: dict[str, int] = {}

        def rebuild(m: "re.Match[str]") -> str:
            nonlocal number, converted
            memo_id = _memo_param(m.group("params"), "ID")
            if memo_id not in bodies:
                return m.group(0)  # 본문을 찾지 못한 메모는 그대로 둔다
            number += 1
            field_id = (
                int(memo_id)
                if memo_id.isdigit() and 0 < int(memo_id) < 2**31
                else 1_900_000_000
            )
            while field_id in used_ids:
                field_id += 1
            used_ids.add(field_id)
            old_id = re.search(r'\bid="([^"]*)"', m.group("attrs"))
            if old_id:
                end_ids[old_id.group(1)] = field_id
            raw_author = html.unescape(_memo_param(m.group("params"), "Author"))
            author = _SAFE_AUTHOR_RE.sub("", raw_author)
            if author != raw_author:
                print(
                    f"[WARN] 작성자 {raw_author!r} → {author!r}: 한/글이 메모를 깨뜨리는 글자를 뺐다",
                    file=sys.stderr,
                )
            author = escape(author)
            try:
                created = datetime.strptime(
                    _memo_param(m.group("params"), "CreateDateTime"),
                    "%Y-%m-%d %H:%M:%S",
                )
            except ValueError:
                created = datetime.now()
            filetime = int((created.timestamp() + 11644473600) * 10_000_000)
            paragraphs = "".join(
                f'<hp:p id="0" paraPrIDRef="{para_pr}" styleIDRef="{style_id}" pageBreak="0" columnBreak="0" merged="0">'
                + (
                    f'<hp:run charPrIDRef="{char_pr}"><hp:t>{line}</hp:t></hp:run>'
                    if line
                    else f'<hp:run charPrIDRef="{char_pr}"/>'
                )
                + "</hp:p>"
                for line in bodies[memo_id].split("\n")
            )
            done.add(memo_id)
            converted += 1
            return (
                f'<hp:fieldBegin id="{field_id}" type="MEMO" name="" editable="1" dirty="1" zorder="{number}"'
                f' fieldid="{MEMO_CTRL_ID}" metaTag="">'
                '<hp:parameters cnt="7" name="">'
                '<hp:integerParam name="Prop">0</hp:integerParam>'
                f'<hp:stringParam name="Command">MEMO/65535/{number}/{filetime & 0xFFFFFFFF}/{filetime >> 32}'
                f"/{author}/\\;;</hp:stringParam>"
                f'<hp:stringParam name="ID">memo{number}</hp:stringParam>'
                f'<hp:integerParam name="Number">{number}</hp:integerParam>'
                f'<hp:stringParam name="Author">{author}</hp:stringParam>'
                '<hp:stringParam name="MemoShapeIDRef">65535</hp:stringParam>'
                f'<hp:stringParam name="CreateDateTime">{created:%Y-%m-%dT%H:%M:%S}Z</hp:stringParam>'
                "</hp:parameters>"
                '<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="TOP" linkListIDRef="0"'
                ' linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">'
                f"{paragraphs}</hp:subList></hp:fieldBegin>"
            )

        xml = _PY_MEMO_FIELD_RE.sub(rebuild, xml)
        for old_id, field_id in end_ids.items():
            xml = re.sub(
                rf'<hp:fieldEnd\b[^>]*\bbeginIDRef="{re.escape(old_id)}"[^>]*/>',
                f'<hp:fieldEnd beginIDRef="{field_id}" fieldid="{MEMO_CTRL_ID}"/>',
                xml,
            )

        def prune(m: "re.Match[str]") -> str:
            rest = _MEMO_RE.sub(
                lambda memo: "" if memo.group(1) in done else memo.group(0), m.group(0)
            )
            return rest if "<hp:memo " in rest else ""  # 다 옮긴 묶음은 지운다

        out[name] = _MEMOGROUP_RE.sub(prune, xml)
    return out, converted


def _postprocess_zip(hwpx_path: str) -> tuple[int, int]:
    """저장된 hwpx 의 section*.xml 을 후처리한다(in-place). 반환: (한/글 모양으로 바꾼 메모 수, 더미 줄 기록 수).

    1. python-hwpx 가 쓴 메모를 한/글이 읽는 모양으로 바꾼다(:func:`memos_to_hancom_shape`).
    2. `add_memo_with_anchor` 가 새 paragraph 를 만들면서 lineSegArray 를 비워두는 경우가 있어
       polaris-dvc strict (JID 11004) 가 깨진다. 더미 lineSegArray 를 넣어 무해하게 보정한다.
    """
    injected = 0
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".hwpx", dir=os.path.dirname(hwpx_path))
    os.close(tmp_fd)
    try:
        with zipfile.ZipFile(hwpx_path, "r") as zin:
            sections: dict[str, str] = {}
            header_xml = ""
            for info in zin.infolist():
                name_lower = info.filename.lower().replace("\\", "/")
                try:
                    if "/section" in name_lower and name_lower.endswith(".xml"):
                        sections[info.filename] = zin.read(info.filename).decode(
                            "utf-8"
                        )
                    elif name_lower.endswith("/header.xml"):
                        header_xml = zin.read(info.filename).decode("utf-8")
                except UnicodeDecodeError:
                    pass
            sections, converted = memos_to_hancom_shape(sections, header_xml)
            with zipfile.ZipFile(
                tmp_path, "w", compression=zipfile.ZIP_DEFLATED
            ) as zout:
                for info in zin.infolist():
                    if info.filename in sections:
                        new_text, n = inject_dummy_linesegs(sections[info.filename])
                        injected += n
                        data = new_text.encode("utf-8")
                    else:
                        data = zin.read(info.filename)
                    info_out = info
                    if info.filename == "mimetype":
                        info_out = zipfile.ZipInfo(info.filename)
                        info_out.compress_type = zipfile.ZIP_STORED
                    zout.writestr(info_out, data)
        shutil.move(tmp_path, hwpx_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
    return converted, injected


def _iter_paragraphs(paragraphs):
    """문단과 그 안 표 칸의 문단을 문서 순서로 낸다."""
    for para in paragraphs:
        yield para
        for table in para.tables:
            for row in table.rows:
                for cell in row.cells:
                    yield from _iter_paragraphs(cell.paragraphs)


def add_memos_batch(
    input_path: str,
    output_path: str,
    memos: list[dict[str, Any]],
) -> int:
    """메모 batch 삽입. 추가된 메모 수 반환."""
    from hwpx import HwpxDocument

    added = 0
    with HwpxDocument.open(input_path) as doc:
        sections = list(doc.sections)
        for memo_spec in memos:
            text = memo_spec.get("text")
            if not text:
                print(
                    f"[WARN] memo without text, skipped: {memo_spec!r}",
                    file=sys.stderr,
                )
                continue

            kwargs: dict[str, Any] = {"text": text}
            if "author" in memo_spec and memo_spec["author"]:
                kwargs["author"] = memo_spec["author"]

            # 위치 지정: paragraph_text 가 우선, 없으면 section/paragraph 인덱스
            if "paragraph_text" in memo_spec and memo_spec["paragraph_text"]:
                # python-hwpx 의 paragraph_text 인자는 「찾기」가 아니라 문서 끝에 그 글로 새 문단을 만든다.
                # 여기서 그 글이 든 첫 문단(표 칸 안 포함)을 찾아 넘긴다
                needle = memo_spec["paragraph_text"]
                target = next(
                    (
                        para
                        for sec in sections
                        for para in _iter_paragraphs(sec.paragraphs)
                        if needle in (para.text or "")
                    ),
                    None,
                )
                if target is None:
                    print(
                        f"[WARN] paragraph_text {needle!r} 가 든 문단이 없다. skipped",
                        file=sys.stderr,
                    )
                    continue
                kwargs["paragraph"] = target
            else:
                section_idx = memo_spec.get("section", 0)
                para_idx = memo_spec.get("paragraph")
                if para_idx is None:
                    print(
                        f"[WARN] memo without paragraph index or paragraph_text, skipped: {memo_spec!r}",
                        file=sys.stderr,
                    )
                    continue
                if section_idx >= len(sections):
                    print(
                        f"[WARN] section_index {section_idx} 가 범위 밖 (총 {len(sections)}). skipped",
                        file=sys.stderr,
                    )
                    continue
                paragraphs = list(sections[section_idx].paragraphs)
                if para_idx >= len(paragraphs):
                    print(
                        f"[WARN] paragraph {para_idx} 범위 밖 (sec {section_idx} 총 {len(paragraphs)}). skipped",
                        file=sys.stderr,
                    )
                    continue
                kwargs["paragraph"] = paragraphs[para_idx]

            try:
                doc.add_memo_with_anchor(**kwargs)
                added += 1
            except Exception as exc:
                print(
                    f"[WARN] add_memo failed for {memo_spec!r}: {exc}", file=sys.stderr
                )

        doc.save_to_path(output_path)

    # save 직후 후처리: 메모를 한/글이 읽는 모양으로, lineSegArray 보정 (polaris strict JID 11004 방지)
    converted, injected = _postprocess_zip(output_path)
    if converted != added:
        print(
            f"[WARN] 한/글 모양으로 바꾼 메모 {converted}개 ≠ 추가한 메모 {added}개",
            file=sys.stderr,
        )
    if injected:
        print(f"[NS] lineseg dummy injected: {injected}", file=sys.stderr)
    return added


def _parse_memos_arg(value: str) -> list[dict[str, Any]]:
    if value == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(value).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("memos JSON must be a list of objects")
    return data


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="HWPX 문서에 첨삭 메모를 batch 삽입한다 (학생 작품 평가용)."
    )
    p.add_argument("input_hwpx", help="입력 .hwpx 경로")
    p.add_argument("output_hwpx", help="출력 .hwpx 경로")
    p.add_argument(
        "--memos",
        required=True,
        help="메모 JSON 파일 경로 (또는 stdin: '-')",
    )
    p.add_argument(
        "--default-author",
        default=None,
        help="memo 객체에 author 가 없을 때 사용할 기본 작성자",
    )
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)

    in_path = Path(args.input_hwpx).resolve()
    if not in_path.exists():
        print(f"[ERR] file not found: {in_path}", file=sys.stderr)
        return 2

    try:
        memos = _parse_memos_arg(args.memos)
    except Exception as exc:
        print(f"[ERR] memos JSON parse failed: {exc}", file=sys.stderr)
        return 2

    if args.default_author:
        for m in memos:
            m.setdefault("author", args.default_author)

    out_path = Path(args.output_hwpx).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    added = add_memos_batch(str(in_path), str(out_path), memos)
    print(f"[OK] {added}/{len(memos)}개 메모 추가 → {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
