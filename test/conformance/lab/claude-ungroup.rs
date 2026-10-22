//! 개발용(임시): 묶음 풀기 전후로 그 쪽 SVG 의 그림(image)과 글자(text) 위치를 견준다.
//!   claude-ungroup <파일> <구역> <문단> <개체> <쪽>
use rhwp::document_core::DocumentCore;

fn items(svg: &str) -> Vec<String> {
    let mut out = Vec::new();
    for (i, _) in svg.match_indices("<image ") {
        let end = svg[i..].find('>').map(|e| i + e).unwrap_or(svg.len());
        let tag = &svg[i..end];
        let get = |k: &str| -> String {
            tag.find(&format!(" {k}=\""))
                .map(|p| {
                    let r = &tag[p + k.len() + 3..];
                    r[..r.find('"').unwrap_or(0)].to_string()
                })
                .unwrap_or_default()
        };
        out.push(format!("image x={} y={} w={} h={}", get("x"), get("y"), get("width"), get("height")));
    }
    for ch in ["1", "교", "기"] {
        if let Some(e) = svg.find(&format!(">{ch}</text>")) {
            let s = svg[..e].rfind("<text ").unwrap();
            let tag = &svg[s..e];
            let pos = tag.find("translate(").map(|p| &tag[p + 10..]).map(|r| r[..r.find(')').unwrap()].to_string());
            let xy = pos.unwrap_or_else(|| {
                let x = tag.find(" x=\"").map(|p| &tag[p + 4..]).map(|r| r[..r.find('"').unwrap()].to_string()).unwrap_or_default();
                let y = tag.find(" y=\"").map(|p| &tag[p + 4..]).map(|r| r[..r.find('"').unwrap()].to_string()).unwrap_or_default();
                format!("{x},{y}")
            });
            out.push(format!("글자 {ch} @ {xy}"));
        }
    }
    out
}

fn main() {
    let a: Vec<String> = std::env::args().collect();
    let bytes = std::fs::read(&a[1]).unwrap();
    let n: Vec<usize> = a[2..6].iter().map(|s| s.parse().unwrap()).collect();
    let mut doc = DocumentCore::from_bytes(&bytes).unwrap();
    let before = items(&doc.render_page_svg_native(n[3] as u32).unwrap());
    let r = doc.ungroup_shape_native(n[0], n[1], n[2]);
    println!("풀기 {:?}", r.map_err(|e| e.to_string()));
    for (k, c) in doc.document().sections[n[0]].paragraphs[n[1]].controls.iter().enumerate() {
        if let rhwp::model::control::Control::Shape(s) = c {
            let cm = s.common();
            let sa = s.shape_attr();
            println!(
                "개체 {k}: x={} y={} w={} h={} 가로기준={:?} 세로기준={:?} 배치={:?} 글자처럼={} attr={:#x} | sa ow={} cw={} sx={} tx={}",
                cm.horizontal_offset, cm.vertical_offset, cm.width, cm.height, cm.horz_rel_to, cm.vert_rel_to, cm.text_wrap, cm.treat_as_char, cm.attr,
                sa.original_width, sa.current_width, sa.render_sx, sa.render_tx
            );
        }
    }
    let after = items(&doc.render_page_svg_native(n[3] as u32).unwrap());
    println!("전: {:#?}\n후: {:#?}", before, after);
}
