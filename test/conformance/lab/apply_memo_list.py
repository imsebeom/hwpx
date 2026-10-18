"""개발용: HWP5 구역 끝의 메모 목록(MEMO_LIST)을 읽어 메모 필드에 본문을 붙인다.

    python apply_memo_list.py [--revert]

근거(2026-10-19 사용자 보고 「hwp 를 hwpx 로 바꾸는 기존 변환기가 메모 본문을 버리고 있었다」): 한/글이 저장한 .hwp 는 구역 마지막
문단 뒤에 MEMO_LIST(레벨 1, 메모 번호 u32) → LIST_HEADER(레벨 1, 문단 수) → 메모 본문 문단(레벨 1)을 메모마다 둔다(블랙박스: 메모 둘을
단 hwpx 를 한/글로 hwp 저장해 레코드를 찍어 봄). 파서는 메모 필드(%me)의 메모 번호만 읽고 이 목록을 읽지 않아 memo_paragraphs 가
비었다 — hwpx 로 내보내면 메모 표지(fieldBegin MEMO)와 작성자만 남고 본문이 사라졌다(rhwp CLI 0.8.6 변환과 에디터 모두).
저장 쪽(serializer/body_text.rs)은 같은 꼴로 쓴다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_use_font_space import SRC  # noqa: E402

TAG = "[claude-hwpx memo-list-hwp5]"

CALL_FIND = """    link_orphan_field_ends(&mut section.paragraphs);
"""
CALL_REPL = f"""    link_orphan_field_ends(&mut section.paragraphs);
    // {TAG} 구역 끝 메모 목록의 본문을 메모 필드에 붙인다
    claude_attach_memo_lists(&records, &mut section.paragraphs);
"""

FN_FIND = """/// 다단락 필드의 종료 마커에 짝 `fieldBegin` 의 id 를 채운다.
"""
FN_REPL = f"""/// {TAG} 구역 끝 MEMO_LIST(메모 번호) → LIST_HEADER → 같은 레벨 문단들을 읽어, 같은 메모 번호의 메모 필드에 본문으로 붙인다.
/// 표 칸, 글상자 안 메모 필드도 찾는다. 이미 본문이 있는 필드는 건드리지 않는다.
fn claude_attach_memo_lists(records: &[Record], paragraphs: &mut [Paragraph]) {{
    use crate::model::control::FieldType;
    use std::collections::HashMap;

    let mut lists: HashMap<u32, Vec<Paragraph>> = HashMap::new();
    let mut i = 0;
    while i < records.len() {{
        if records[i].tag_id != tags::HWPTAG_MEMO_LIST || records[i].data.len() < 4 {{
            i += 1;
            continue;
        }}
        let level = records[i].level;
        let d = &records[i].data;
        let index = u32::from_le_bytes([d[0], d[1], d[2], d[3]]);
        i += 1;
        if i < records.len()
            && records[i].tag_id == tags::HWPTAG_LIST_HEADER
            && records[i].level == level
        {{
            i += 1;
        }}
        let mut paras = Vec::new();
        while i < records.len()
            && records[i].tag_id == tags::HWPTAG_PARA_HEADER
            && records[i].level == level
        {{
            let start = i;
            i += 1;
            while i < records.len() && records[i].level > level {{
                i += 1;
            }}
            if let Ok(p) = parse_paragraph(&records[start..i]) {{
                paras.push(p);
            }}
        }}
        if !paras.is_empty() {{
            lists.entry(index).or_insert(paras);
        }}
    }}
    if lists.is_empty() {{
        return;
    }}

    fn walk(paras: &mut [Paragraph], lists: &HashMap<u32, Vec<Paragraph>>, depth: usize) {{
        if depth > 8 {{
            return;
        }}
        for para in paras.iter_mut() {{
            for ctrl in para.controls.iter_mut() {{
                match ctrl {{
                    Control::Field(f) => {{
                        // 한/글 저장본의 메모 필드는 %me 가 아니라 %unk 이고 명령이 「MEMO/」로 시작한다(실측)
                        let is_memo = f.field_type == FieldType::Memo || f.command.starts_with("MEMO/");
                        if is_memo && f.memo_index != 0 && f.memo_paragraphs.is_empty() {{
                            if let Some(body) = lists.get(&f.memo_index) {{
                                f.memo_paragraphs = body.clone();
                            }}
                        }}
                    }}
                    Control::Table(t) => {{
                        for cell in t.cells.iter_mut() {{
                            walk(&mut cell.paragraphs, lists, depth + 1);
                        }}
                    }}
                    Control::Shape(shape) => {{
                        if let Some(tb) = shape.drawing_mut().and_then(|d| d.text_box.as_mut()) {{
                            walk(&mut tb.paragraphs, lists, depth + 1);
                        }}
                    }}
                    _ => {{}}
                }}
            }}
        }}
    }}
    walk(paragraphs, &lists, 0);
}}

/// 다단락 필드의 종료 마커에 짝 `fieldBegin` 의 id 를 채운다.
"""

SER_FIND = """            if let Some(memo_children) = super::field::memo_field_children_xml(f) {
                out.push_str(&super::field::field_begin_open_tag(f));
                out.push('>');
                out.push_str(&memo_children);
"""
SER_REPL = f"""            if let Some(memo_children) = super::field::memo_field_children_xml(f) {{
                out.push_str(&super::field::field_begin_open_tag(f));
                out.push('>');
                // {TAG} 이 갈래는 빈 본문을 고정으로 쓴다. HWP5 메모 목록에서 읽은 본문이 있으면 그 문단을 쓴다
                if f.memo_paragraphs.is_empty() {{
                    out.push_str(&memo_children);
                }} else {{
                    let params_end = memo_children.find("<hp:subList").unwrap_or(memo_children.len());
                    out.push_str(&memo_children[..params_end]);
                    out.push_str(&render_sub_list_open(f.memo_text_direction.as_deref()));
                    let mut vert_cursor: u32 = 0;
                    for para in &f.memo_paragraphs {{
                        ctx.para_shape_ids.reference(para.para_shape_id);
                        let sid = ctx.effective_style_id(para.style_id);
                        ctx.style_ids.reference(sid as u16);
                        let (runs, linesegs, advance) = render_paragraph_parts(para, vert_cursor, ctx);
                        vert_cursor = advance;
                        let pid = ctx.next_para_id();
                        out.push_str(&render_hp_p_open(para, pid, sid));
                        out.push_str(&runs);
                        out.push_str(&linesegs);
                        out.push_str("</hp:p>");
                    }}
                    out.push_str("</hp:subList>");
                }}
"""

EDITS = [
    ("parser/body_text.rs", CALL_FIND, CALL_REPL),
    ("parser/body_text.rs", FN_FIND, FN_REPL),
    ("serializer/hwpx/section.rs", SER_FIND, SER_REPL),
]


def main():
    revert = "--revert" in sys.argv
    edits = list(reversed(EDITS)) if revert else EDITS
    for rel, find, repl in edits:
        if revert:
            find, repl = repl, find
        f = SRC / rel
        raw = f.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        s = raw.replace("\r\n", "\n")
        if (find not in s) if revert else (repl in s):
            print("이미", rel)
            continue
        n = s.count(find)
        if n != 1:
            sys.exit(f"{rel}: 자리 {n}곳 — {find[:60]!r}")
        s = s.replace(find, repl)
        f.write_bytes(s.replace("\n", nl).encode("utf-8"))
        print("넣음", rel)


if __name__ == "__main__":
    main()
