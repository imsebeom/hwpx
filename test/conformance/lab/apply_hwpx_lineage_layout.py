"""개발용: 에디터가 hwpx 에서 내보낸 hwp(표지 /RhwpHwpxOrigin)도 hwpx 조판 규칙으로 열고, 칸 안 메모 본문도 hwp 에 쓴다.

    python apply_hwpx_lineage_layout.py [--revert]

근거(결과보고서 사본, 2026-10-30): 내보낸 hwp 를 다시 열면 내용은 같은데 56쪽(원본 49쪽). 다시 연 문서의 형식 표지만 hwpx 로 바꾸면 49쪽,
끝 문단을 빼는 것은 쪽수와 무관했다. 한/글이 저장한 hwp 에는 이 표지가 없어 바뀌지 않는다.
메모 본문은 표식 14개 중 6개만 남았다. 본문 최상위 문단만 모아 칸 안 메모 8개를 빠뜨렸다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx hwpx-lineage-layout]"
TAG2 = "[claude-hwpx memo-list-cells]"

EDITS = [
    (
        "model/document.rs",
        "            self.provenance.format == SourceFormat::Hwpx && !native_hwp3_hwpx,\n            hwp5_origin_hwpx,\n",
        (
            f"            // {TAG} 에디터가 hwpx 에서 내보낸 hwp 는 같은 문서다. 같은 규칙으로 조판해야 쪽수가 안 바뀐다\n"
            "            (self.provenance.format == SourceFormat::Hwpx && !native_hwp3_hwpx) || self.provenance.hwpx_lineage,\n"
            "            hwp5_origin_hwpx,\n"
        ),
    ),
    (
        "serializer/body_text.rs",
        (
            "    let mut memo_lists = Vec::new();\n"
            "    for para in &section.paragraphs {\n"
            "        for ctrl in &para.controls {\n"
            "            if let Control::Field(field) = ctrl {\n"
            "                if field.field_type == crate::model::control::FieldType::Memo\n"
            "                    && !field.memo_paragraphs.is_empty()\n"
            "                {\n"
            "                    memo_lists.push((field.memo_index, field.memo_paragraphs.clone()));\n"
            "                }\n"
            "            }\n"
            "        }\n"
            "    }\n"
            "    memo_lists\n"
            "}\n"
        ),
        (
            f"    // {TAG2} 표 칸(표 속 표 포함) 안의 메모도 모은다. 안 그러면 다시 열 때 본문이 사라진다\n"
            "    fn walk(paras: &[Paragraph], out: &mut Vec<(u32, Vec<Paragraph>)>) {\n"
            "        for para in paras {\n"
            "            for ctrl in &para.controls {\n"
            "                match ctrl {\n"
            "                    Control::Field(field)\n"
            "                        if (field.field_type == crate::model::control::FieldType::Memo\n"
            '                            || field.command.starts_with("MEMO/"))\n'
            "                            && !field.memo_paragraphs.is_empty() =>\n"
            "                    {\n"
            "                        out.push((field.memo_index, field.memo_paragraphs.clone()));\n"
            "                    }\n"
            "                    Control::Table(t) => {\n"
            "                        for cell in &t.cells {\n"
            "                            walk(&cell.paragraphs, out);\n"
            "                        }\n"
            "                    }\n"
            "                    _ => {}\n"
            "                }\n"
            "            }\n"
            "        }\n"
            "    }\n"
            "    let mut memo_lists = Vec::new();\n"
            "    walk(&section.paragraphs, &mut memo_lists);\n"
            "    memo_lists\n"
            "}\n"
        ),
    ),
]


def main():
    revert = "--revert" in sys.argv
    edits = list(reversed(EDITS)) if revert else EDITS
    for rel, find, repl in edits:
        p = SRC / rel
        raw = p.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        s = raw.replace("\r\n", "\n")
        a, b = (repl, find) if revert else (find, repl)
        assert s.count(a) == 1, (rel, a[:70], s.count(a))
        p.write_bytes(s.replace(a, b).replace("\n", nl).encode("utf-8"))
    print("되돌림" if revert else "적용")


if __name__ == "__main__":
    main()
