//! 개발용(임시): 선택 [o, o+3] 의 첫 사각형 왼쪽, 끝 사각형 오른쪽을 캐럿 o, o+3 과 견준다.
//! claude-seldbg <파일> body <문단> | cell <문단> <컨트롤> <칸>
use rhwp::wasm_api::HwpDocument;
use serde_json::Value;

fn main() {
    let a: Vec<String> = std::env::args().collect();
    let bytes = std::fs::read(&a[1]).unwrap();
    let body = a[2] == "body";
    let n: Vec<u32> = a[3..].iter().map(|s| s.parse().unwrap()).collect();
    let doc = HwpDocument::from_bytes(&bytes).unwrap();
    let (p, ci, cell) = (n[0], n.get(1).copied().unwrap_or(0), n.get(2).copied().unwrap_or(0));
    let len = if body {
        doc.get_paragraph_length(0, p).unwrap()
    } else {
        doc.get_cell_paragraph_length(0, p, ci, cell, 0).unwrap()
    };
    let caret = |o: u32| -> Value {
        let s = if body {
            doc.get_cursor_rect(0, p, o).ok().unwrap()
        } else {
            doc.get_cursor_rect_in_cell(0, p, ci, cell, 0, o).ok().unwrap()
        };
        serde_json::from_str(&s).unwrap()
    };
    let sel = |x: u32, y: u32| -> Vec<Value> {
        let s = if body {
            doc.get_selection_rects(0, p, x, p, y).ok().unwrap()
        } else {
            doc.get_selection_rects_in_cell(0, p, ci, cell, 0, x, 0, y).ok().unwrap()
        };
        serde_json::from_str(&s).unwrap()
    };
    let f = |v: &Value, k: &str| v[k].as_f64().unwrap();
    let mut bad = 0;
    for o in 0..len.saturating_sub(2) {
        let (c, c2, r) = (caret(o), caret(o + 3), sel(o, o + 3));
        if r.is_empty() {
            bad += 1;
            println!("{o} no rect");
            continue;
        }
        let (r0, rl) = (&r[0], &r[r.len() - 1]);
        let ok_l = (f(r0, "x") - f(&c, "x")).abs() < 1.5 && (f(r0, "y") - f(&c, "y")).abs() < 4.0;
        let ok_r = (f(rl, "x") + f(rl, "width") - f(&c2, "x")).abs() < 1.5;
        if !ok_l || !ok_r {
            bad += 1;
            let rs: Vec<String> = r
                .iter()
                .map(|q| format!("{:.1},{:.1}+{:.1}", f(q, "x"), f(q, "y"), f(q, "width")))
                .collect();
            println!(
                "{o} caret {:.1},{:.1} -> {:.1},{:.1} rects {}",
                f(&c, "x"),
                f(&c, "y"),
                f(&c2, "x"),
                f(&c2, "y"),
                rs.join(" ")
            );
        }
    }
    println!("len {len} bad {bad}");
}
