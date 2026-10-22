//! 개발용(임시): 묶음 안 글상자 편집 시험. 쪽 SVG 에서 찾을 글자의 n 번째 자리를 눌러(hit_test) 받은 위치로 글을 넣고,
//! 그 글상자 문단 글이 바뀌는지와 다시 그린 쪽에 넣은 글이 보이는지 본다.
//!   claude-grouptb <파일> <쪽> <찾을 글자> <넣을 글> [n=0]
use rhwp::document_core::DocumentCore;
use serde_json::Value;

fn main() {
    let a: Vec<String> = std::env::args().collect();
    let bytes = std::fs::read(&a[1]).unwrap();
    let page: u32 = a[2].parse().unwrap();
    let needle = &a[3];
    let ins = &a[4];
    let nth: usize = a.get(5).and_then(|s| s.parse().ok()).unwrap_or(0);
    let mut doc = DocumentCore::from_bytes(&bytes).unwrap();
    let svg = doc.render_page_svg_native(page).unwrap();
    let pat = format!(">{}</text>", needle);
    let end = svg.match_indices(&pat).nth(nth).map(|(i, _)| i).expect("글자를 못 찾음");
    let start = svg[..end].rfind("<text ").unwrap();
    let tag = &svg[start..end];
    let num = |key: &str| -> Option<f64> {
        let i = tag.find(key)? + key.len();
        let rest = &tag[i..];
        let j = rest.find(|c: char| !(c.is_ascii_digit() || c == '.' || c == '-'))?;
        rest[..j].parse().ok()
    };
    let (x, y): (f64, f64) = if let Some(i) = tag.find("translate(") {
        let rest = &tag[i + 10..];
        let comma = rest.find(',').unwrap();
        let close = rest.find(')').unwrap();
        (rest[..comma].parse().unwrap(), rest[comma + 1..close].parse().unwrap())
    } else {
        (num("x=\"").unwrap(), num("y=\"").unwrap())
    };
    let hit = doc.hit_test_native(page, x + 2.0, y - 4.0).unwrap();
    println!("누름 ({x:.1},{y:.1}) → {hit}");
    let h: Value = serde_json::from_str(&hit).unwrap();
    let sec = h["sectionIndex"].as_u64().unwrap() as usize;
    let ppi = h["parentParaIndex"].as_u64().expect("글상자 안이 아님") as usize;
    let ci = h["controlIndex"].as_u64().unwrap() as usize;
    let cell = h["cellIndex"].as_u64().unwrap() as usize;
    let cpi = h["cellParaIndex"].as_u64().unwrap() as usize;
    let off = h["charOffset"].as_u64().unwrap() as usize;
    let before = doc.get_text_in_cell_native(sec, ppi, ci, cell, cpi, 0, 100);
    let r = doc.insert_text_in_cell_native(sec, ppi, ci, cell, cpi, off, ins);
    let after = doc.get_text_in_cell_native(sec, ppi, ci, cell, cpi, 0, 100);
    println!("넣기 결과 {:?}", r.as_ref().map(|_| "ok").map_err(|e| e.to_string()));
    println!("전 {:?}\n후 {:?}", before.map_err(|e| e.to_string()), after.map_err(|e| e.to_string()));
    let svg2 = doc.render_page_svg_native(page).unwrap();
    let first = ins.chars().next().unwrap();
    println!("다시 그린 쪽에 넣은 글 있음: {}", svg2.contains(&format!(">{}</text>", first)));
}
