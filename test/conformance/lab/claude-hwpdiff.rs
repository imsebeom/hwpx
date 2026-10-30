// 진단: 문서를 hwp 로 내보내 다시 열고 모델을 원본과 견준다(임시)
use rhwp::document_core::DocumentCore;
use rhwp::model::control::Control;
use rhwp::model::paragraph::Paragraph;
use std::collections::BTreeMap;
#[derive(Default)]
struct D { n: BTreeMap<String, usize>, ex: BTreeMap<String, Vec<String>> }
impl D { fn hit(&mut self, k: &str, e: String) { *self.n.entry(k.into()).or_default() += 1; let v = self.ex.entry(k.into()).or_default(); if v.len() < 4 { v.push(e); } } }
fn memos(ps: &[Paragraph]) -> usize { let mut c = 0; for p in ps { for x in &p.controls { match x { Control::Field(f) if f.field_type == rhwp::model::control::FieldType::Memo => c += 1, Control::Table(t) => for cell in &t.cells { c += memos(&cell.paragraphs); }, _ => {} } } } c }
fn para(a: &Paragraph, b: &Paragraph, at: &str, d: &mut D) {
    if a.text != b.text { d.hit("글", format!("{at} {:?} / {:?}", a.text.chars().take(30).collect::<String>(), b.text.chars().take(30).collect::<String>())); }
    if a.char_count != b.char_count { d.hit("char_count", format!("{at} {} {}", a.char_count, b.char_count)); }
    if a.para_shape_id != b.para_shape_id { d.hit("문단모양", format!("{at} {} {}", a.para_shape_id, b.para_shape_id)); }
    if a.char_offsets != b.char_offsets { d.hit("char_offsets", at.to_string()); }
    if a.char_shapes.len() != b.char_shapes.len() { d.hit("글자모양수", format!("{at} {} {}", a.char_shapes.len(), b.char_shapes.len())); }
    if a.line_segs.len() != b.line_segs.len() { d.hit("줄수", format!("{at} {} {}", a.line_segs.len(), b.line_segs.len())); }
    else { for (i, (x, y)) in a.line_segs.iter().zip(&b.line_segs).enumerate() {
        if x.text_start != y.text_start { d.hit("줄시작", format!("{at} 줄{i} {} {}", x.text_start, y.text_start)); }
        if x.vertical_pos != y.vertical_pos { d.hit("vpos", format!("{at} 줄{i} {} {}", x.vertical_pos, y.vertical_pos)); }
        if x.line_height != y.line_height { d.hit("줄높이", format!("{at} 줄{i} {} {}", x.line_height, y.line_height)); }
        if x.line_spacing != y.line_spacing { d.hit("줄간격", format!("{at} 줄{i} {} {}", x.line_spacing, y.line_spacing)); }
    } }
    if a.controls.len() != b.controls.len() { d.hit("컨트롤수", format!("{at} {} {}", a.controls.len(), b.controls.len())); return; }
    for (i, (x, y)) in a.controls.iter().zip(&b.controls).enumerate() {
        if std::mem::discriminant(x) != std::mem::discriminant(y) { d.hit("컨트롤종류", format!("{at} c{i}")); continue; }
        if let (Control::Table(s), Control::Table(t)) = (x, y) {
            let w = format!("{at} 표{i}");
            if s.common.height != t.common.height { d.hit("표높이", format!("{w} {} {}", s.common.height, t.common.height)); }
            if s.common.width != t.common.width { d.hit("표폭", format!("{w} {} {}", s.common.width, t.common.width)); }
            if s.common.treat_as_char != t.common.treat_as_char { d.hit("글자처럼", w.clone()); }
            if s.common.vertical_offset != t.common.vertical_offset { d.hit("표세로오프셋", format!("{w} {} {}", s.common.vertical_offset, t.common.vertical_offset)); }
            if (s.outer_margin_top, s.outer_margin_bottom) != (t.outer_margin_top, t.outer_margin_bottom) { d.hit("표바깥여백", format!("{w} {:?} {:?}", (s.outer_margin_top, s.outer_margin_bottom), (t.outer_margin_top, t.outer_margin_bottom))); }
            if s.page_break != t.page_break { d.hit("표쪽나눔", format!("{w} {:?} {:?}", s.page_break, t.page_break)); }
            if s.attr != t.attr { d.hit("표attr", format!("{w} {:x} {:x}", s.attr, t.attr)); }
            if s.cell_spacing != t.cell_spacing { d.hit("칸간격", w.clone()); }
            if s.padding.top != t.padding.top || s.padding.bottom != t.padding.bottom { d.hit("표안여백", w.clone()); }
            if s.row_sizes != t.row_sizes { d.hit("row_sizes", w.clone()); }
            if s.caption.is_some() != t.caption.is_some() { d.hit("캡션", w.clone()); }
            if s.cells.len() != t.cells.len() { d.hit("칸수", w.clone()); continue; }
            for (ci, (c, e)) in s.cells.iter().zip(&t.cells).enumerate() {
                let cw = format!("{w} 칸{ci}");
                if c.height != e.height { d.hit("칸높이", format!("{cw} {} {}", c.height, e.height)); }
                if c.width != e.width { d.hit("칸폭", format!("{cw} {} {}", c.width, e.width)); }
                if (c.padding.top, c.padding.bottom) != (e.padding.top, e.padding.bottom) { d.hit("칸여백", cw.clone()); }
                if c.apply_inner_margin != e.apply_inner_margin { d.hit("칸여백적용", cw.clone()); }
                if c.paragraphs.len() != e.paragraphs.len() { d.hit("칸문단수", format!("{cw} {} {}", c.paragraphs.len(), e.paragraphs.len())); continue; }
                for (pi, (p, q)) in c.paragraphs.iter().zip(&e.paragraphs).enumerate() { para(p, q, &format!("{cw} p{pi}"), d); }
            }
        }
    }
}
fn main() {
    let path = std::env::args().nth(1).unwrap();
    let data = std::fs::read(&path).unwrap();
    let a = DocumentCore::from_bytes(&data).unwrap();
    let raw = a.export_hwp_native().unwrap();
    let out = std::env::args().nth(2);
    if let Some(o) = &out { std::fs::write(o, &raw).unwrap(); }
    let b = DocumentCore::from_bytes(&raw).unwrap();
    println!("쪽수 원본 {} 내보낸 hwp {}, 크기 {}", a.page_count(), b.page_count(), raw.len());
    let (da, db) = (a.document(), b.document());
    println!("구역 {} {}, 글자모양 {} {}, 문단모양 {} {}", da.sections.len(), db.sections.len(), da.doc_info.char_shapes.len(), db.doc_info.char_shapes.len(), da.doc_info.para_shapes.len(), db.doc_info.para_shapes.len());
    let mut d = D::default();
    for (si, (s, t)) in da.sections.iter().zip(&db.sections).enumerate() {
        println!("구역{si} 문단 {} {}, 메모 {} {}", s.paragraphs.len(), t.paragraphs.len(), memos(&s.paragraphs), memos(&t.paragraphs));
        for (pi, (p, q)) in s.paragraphs.iter().zip(&t.paragraphs).enumerate() { para(p, q, &format!("s{si} p{pi}"), &mut d); }
    }
    for (k, v) in &d.n { println!("{k}: {v}"); for e in &d.ex[k] { println!("   {e}"); } }
}
