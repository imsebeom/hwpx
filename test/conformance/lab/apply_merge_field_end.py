"""개발용: 문단을 합칠 때 글 끝에서 닫히는 필드의 끝 표식 8칸을 세고, 줄 시작이 표식 한가운데면 줄 배치를 내보내지 않는다.

    python apply_merge_field_end.py [--revert]

근거(「생캠_과학_문항_평가수정_고영민기준」 _01~_08, 2026-10-30): 메모가 든 칸에 set_cell(합치기, 지우기, 넣기)을 하면
char_count 가 8 모자라 저장기가 메모 표식을 글 뒤로 몰아 쓰고, 표식이 글 앞에 있다고 보고 잰 줄 시작(26 + 8 = 34)은 그대로 나갔다.
글 31자 뒤 fieldBegin 이 31~39 라 34 는 표식 안이다. 한/글은 Open False 로 그 문단이 든 표부터 끝까지 버렸다(17쪽 → 3쪽).
표식 안 줄 시작이 있는 판 8개만 실패하고 없는 판 4개는 정상, 그 문단의 줄 배치만 지우면 17쪽으로 열린다.
"""

import sys
from pathlib import Path

SRC = Path.home() / ".claude" / "skills" / "hwpx" / "editor" / ".build" / "rhwp" / "src"
TAG = "[claude-hwpx merge-field-end]"
TAG2 = "[claude-hwpx seg-inside-slot]"

EDITS = [
    (
        "model/paragraph.rs",
        (
            "            .filter(|&&p| p >= self_text_len)\n"
            "            .count() as u32\n"
            "            * 8;\n"
            "        let utf16_end: u32 = if !self.char_offsets.is_empty() {\n"
        ),
        (
            "            .filter(|&&p| p >= self_text_len)\n"
            "            .count() as u32\n"
            "            * 8\n"
            f"            // {TAG} 글 끝에서 닫히는 필드의 끝 표식도 8칸이다(컨트롤이 아니라 위에서 안 잡힌다)\n"
            "            + self\n"
            "                .field_ranges\n"
            "                .iter()\n"
            "                .filter(|f| f.end_char_idx >= self_text_len)\n"
            "                .count() as u32\n"
            "                * 8;\n"
            "        let utf16_end: u32 = if !self.char_offsets.is_empty() {\n"
        ),
    ),
    (
        "model/paragraph.rs",
        (
            "        self.char_count = self.text.chars().map(Self::char_stream_len).sum::<u32>()\n"
            "            + self.controls.len() as u32 * 8\n"
            "            + 1;\n"
            "\n"
            "        // 7. has_para_text: 병합 후 텍스트/컨트롤이 있으면 PARA_TEXT 필요\n"
        ),
        (
            "        self.char_count = self.text.chars().map(Self::char_stream_len).sum::<u32>()\n"
            "            + self.controls.len() as u32 * 8\n"
            f"            // {TAG} 끝 표식\n"
            "            + (self.field_ranges.len() + self.orphan_field_ends.len()) as u32 * 8\n"
            "            + 1;\n"
            "\n"
            "        // 7. has_para_text: 병합 후 텍스트/컨트롤이 있으면 PARA_TEXT 필요\n"
        ),
    ),
    (
        "serializer/hwpx/section.rs",
        ("        &source_line_segs[..0]\n    } else if line_seg_axis_end > 0 {\n"),
        (
            "        &source_line_segs[..0]\n"
            f"    }} else if line_seg_inside_slot(para, source_line_segs) {{\n"
            f"        // {TAG2} 줄 시작이 컨트롤 8칸 한가운데면 한/글이 그 문단부터 끝까지 버린다(Open False, 17쪽 → 3쪽).\n"
            "        // 빼면 한/글이 열 때 다시 잰다\n"
            "        &source_line_segs[..0]\n"
            "    } else if line_seg_axis_end > 0 {\n"
        ),
    ),
    (
        "serializer/hwpx/section.rs",
        (
            "/// Paragraph 하나를 (완전한 `<hp:run>` 시퀀스 XML, `<hp:linesegarray>` 요소 XML,\n"
        ),
        (
            f"/// {TAG2} 글 사이와 글 뒤의 컨트롤 칸(8칸 단위)을 구해 줄 시작이 그 안쪽을 가리키는지 본다.\n"
            "fn line_seg_inside_slot(para: &Paragraph, segs: &[LineSeg]) -> bool {\n"
            "    let chars: Vec<char> = para.text.chars().collect();\n"
            "    if para.char_offsets.len() != chars.len() {\n"
            "        return false;\n"
            "    }\n"
            "    let mut gaps = Vec::new();\n"
            "    let mut prev_end = 0u32;\n"
            "    for (i, &c) in chars.iter().enumerate() {\n"
            "        let off = para.char_offsets[i];\n"
            "        if off > prev_end {\n"
            "            gaps.push((prev_end, off));\n"
            "        }\n"
            "        prev_end = off + char_utf16_width(c);\n"
            "    }\n"
            "    let end = para.char_count.saturating_sub(1);\n"
            "    if end > prev_end {\n"
            "        gaps.push((prev_end, end));\n"
            "    }\n"
            "    segs.iter().any(|s| {\n"
            "        gaps.iter().any(|&(a, b)| {\n"
            "            (b - a) % 8 == 0 && s.text_start > a && s.text_start < b && (s.text_start - a) % 8 != 0\n"
            "        })\n"
            "    })\n"
            "}\n"
            "\n"
            "/// Paragraph 하나를 (완전한 `<hp:run>` 시퀀스 XML, `<hp:linesegarray>` 요소 XML,\n"
        ),
    ),
]

EDITS.insert(
    2,
    (
        "model/paragraph.rs",
        (
            "        let ctrl_code_units: u32 = self.controls.len() as u32 * 8;\n"
            "        self.char_count = kept_text_code_units + ctrl_code_units + 1; // +1 for paragraph end marker\n"
        ),
        (
            f"        // {TAG} 남은 필드의 끝 표식도 8칸이다\n"
            "        let ctrl_code_units: u32 =\n"
            "            (self.controls.len() + self.field_ranges.len() + self.orphan_field_ends.len()) as u32 * 8;\n"
            "        self.char_count = kept_text_code_units + ctrl_code_units + 1; // +1 for paragraph end marker\n"
        ),
    ),
)


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
