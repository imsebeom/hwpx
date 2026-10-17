//! [claude-hwpx 개발 도구] 문서의 문단마다 엔진이 계산한 줄 시작(getLineStarts 와 같은 값)을 한 줄씩 찍는다.
//! wasm 을 다시 빌드하지 않고 조판 규칙 수정을 빨리 확인하려고 쓴다(줄 배치를 지운 문서를 넣는다).
//!   claude-linestarts <파일>...          → 본문: 「파일\t문단\t[줄 시작]」
//!   CLAUDE_CELLS=1 claude-linestarts ... → 칸까지: 「파일\t칸목록순번:문단\t[줄 시작]」(칸 목록 순번은 isCell 목록 차례)
use rhwp::document_core::DocumentCore;

fn main() {
    let cells = std::env::var("CLAUDE_CELLS").is_ok();
    for path in std::env::args().skip(1) {
        let data = std::fs::read(&path).expect("파일 읽기");
        let core = DocumentCore::from_bytes(&data).expect("문서 열기");
        let cm: serde_json::Value = serde_json::from_str(&core.get_cursor_model_json()).expect("커서 모형");
        println!("{}\tPAGES\t{}", path, core.page_count());
        let n = cm["root"]["paraCount"].as_u64().unwrap_or(0);
        for p in 0..n {
            println!("{}\t{}\t{}", path, p, core.line_starts_json(0, p as usize));
        }
        if cells {
            let lists = cm["lists"].as_array().cloned().unwrap_or_default();
            for (k, l) in lists.iter().filter(|l| l["isCell"].as_bool() == Some(true)).enumerate() {
                let id = l["listId"].as_u64().unwrap_or(0) as u32;
                for p in 0..l["paraCount"].as_u64().unwrap_or(0) {
                    println!("{}\t{}:{}\t{}", path, k, p, core.line_starts_json(id, p as usize));
                }
            }
        }
    }
}
