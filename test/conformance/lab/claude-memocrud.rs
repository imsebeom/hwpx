//! 개발용: 메모 지우기, 본문 고치기(memo-crud) 왕복 시험.
//!   claude-memocrud <파일.hwpx> [최대 메모 수]
//! 메모마다 새로 열어 지우고 → hwpx 로 내보내 → 다시 연다. 다음을 본다.
//!   ① 메모 수가 하나 줄고 나머지 메모(본문, 걸린 글, 작성자)가 그대로 ② 문서 글이 그대로
//!   ③ 고친 IR 과 다시 연 IR 의 문단 위치표(char_offsets, char_count) 차이가 손대지 않은 왕복의 차이보다 늘지 않음
//! 첫 메모의 본문을 고쳐 저장하고 다시 열어 본문이 바뀌었는지도 본다.
use rhwp::document_core::DocumentCore;
use rhwp::model::control::Control;
use rhwp::model::paragraph::Paragraph;

#[derive(PartialEq, Debug, Clone)]
struct P {
    text: String,
    offsets: Vec<u32>,
    count: u32,
}

fn walk(paras: &[Paragraph], out: &mut Vec<P>) {
    for p in paras {
        out.push(P { text: p.text.clone(), offsets: p.char_offsets.clone(), count: p.char_count });
        for c in &p.controls {
            if let Control::Table(t) = c {
                for cell in &t.cells {
                    walk(&cell.paragraphs, out);
                }
            }
        }
    }
}

fn dump(doc: &DocumentCore) -> Vec<P> {
    let mut out = Vec::new();
    for s in &doc.document().sections {
        walk(&s.paragraphs, &mut out);
    }
    out
}

fn memos(doc: &DocumentCore) -> Vec<serde_json::Value> {
    serde_json::from_str(&doc.get_memo_list_json()).unwrap()
}

fn key(m: &serde_json::Value) -> String {
    format!("{}|{}|{}", m["author"], m["anchor"], m["text"])
}

/// 위치표가 다른 문단 수(글은 같아야 한다)
fn offset_diff(a: &[P], b: &[P]) -> (usize, usize) {
    let text = a.iter().zip(b).filter(|(x, y)| x.text != y.text).count() + a.len().abs_diff(b.len());
    let pos = a.iter().zip(b).filter(|(x, y)| x.offsets != y.offsets || x.count != y.count).count();
    (text, pos)
}

fn main() {
    let a: Vec<String> = std::env::args().collect();
    let bytes = std::fs::read(&a[1]).unwrap();
    let cap: usize = a.get(2).and_then(|s| s.parse().ok()).unwrap_or(usize::MAX);
    let doc0 = DocumentCore::from_bytes(&bytes).unwrap();
    let m0 = memos(&doc0);
    let base = DocumentCore::from_bytes(&doc0.export_hwpx_native().unwrap()).unwrap();
    let (bt, bp) = offset_diff(&dump(&doc0), &dump(&base));
    println!("메모 {}개, 손대지 않은 왕복: 글 다른 문단 {}, 위치표 다른 문단 {}", m0.len(), bt, bp);
    let mut bad = 0;
    for (i, m) in m0.iter().enumerate().take(cap) {
        let id = m["fieldId"].as_u64().unwrap() as u32;
        let mut doc = DocumentCore::from_bytes(&bytes).unwrap();
        if let Err(e) = doc.delete_memo(id) {
            println!("[{}] 지우기 실패: {}", i + 1, e);
            bad += 1;
            continue;
        }
        let after = memos(&doc);
        let re = DocumentCore::from_bytes(&doc.export_hwpx_native().unwrap()).unwrap();
        let m2 = memos(&re);
        let want: Vec<String> = m0.iter().enumerate().filter(|(k, _)| *k != i).map(|(_, x)| key(x)).collect();
        let got: Vec<String> = m2.iter().map(key).collect();
        let got_live: Vec<String> = after.iter().map(key).collect();
        let (t_live, _) = offset_diff(&dump(&doc0), &dump(&doc));
        let (t, p) = offset_diff(&dump(&doc), &dump(&re));
        let ok = want == got && want == got_live && t_live == 0 && t <= bt && p <= bp;
        if !ok {
            bad += 1;
        }
        println!(
            "[{}] {} id={} 경로={} 문단 {}..{} | 메모 {}→{}(다시 연 뒤 {}) 같음={} | 글 바뀜 {} | 왕복 글 {} 위치표 {}",
            i + 1,
            if ok { "통과" } else { "실패" },
            id,
            m["path"].as_array().map(|p| p.len()).unwrap_or(0),
            m["startPara"],
            m["endPara"],
            m0.len(),
            after.len(),
            m2.len(),
            want == got && want == got_live,
            t_live,
            t,
            p
        );
    }
    if let Some(m) = m0.first() {
        let id = m["fieldId"].as_u64().unwrap() as u32;
        let mut doc = DocumentCore::from_bytes(&bytes).unwrap();
        doc.update_memo_body(id, "고친 메모\n둘째 줄").unwrap();
        let re = DocumentCore::from_bytes(&doc.export_hwpx_native().unwrap()).unwrap();
        let m2 = memos(&re);
        let ok = m2.len() == m0.len()
            && m2[0]["text"] == "고친 메모\n둘째 줄"
            && m2[0]["author"] == m["author"]
            && m2[0]["anchor"] == m["anchor"]
            && m2.iter().skip(1).map(key).eq(m0.iter().skip(1).map(key));
        if !ok {
            bad += 1;
        }
        println!("고치기: {} (본문 {})", if ok { "통과" } else { "실패" }, m2[0]["text"]);
    }
    println!("실패 {}", bad);
}
