// [claude-hwpx] 메모 목록 확인용(임시).
//   cargo run --example claude_memo -- <in.hwpx> [out.hwpx]
// 메모 목록 JSON 을 찍고, 둘째 인자가 있으면 hwpx 로 다시 내보낸다.
use rhwp::document_core::DocumentCore;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let bytes = std::fs::read(&args[1]).expect("read");
    let core = DocumentCore::from_bytes(&bytes).expect("parse");
    println!("{}", core.get_memo_list_json());
    eprintln!(
        "paragraphs per section: {:?}",
        core.document()
            .sections
            .iter()
            .map(|s| s.paragraphs.len())
            .collect::<Vec<_>>()
    );
    if let Some(out) = args.get(2) {
        std::fs::write(out, core.export_hwpx_native().expect("export")).expect("write");
    }
}
