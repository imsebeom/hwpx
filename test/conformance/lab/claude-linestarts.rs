//! [claude-hwpx 개발 도구] 문서의 문단마다 엔진이 계산한 줄 시작(getLineStarts 와 같은 값)을 한 줄씩 찍는다.
//! wasm 을 다시 빌드하지 않고 조판 규칙 수정을 빨리 확인하려고 쓴다(줄 배치를 지운 문서를 넣는다).
//!   claude-linestarts <파일>...          → 본문: 「파일\t문단\t[줄 시작]」
//!   CLAUDE_CELLS=1 claude-linestarts ... → 칸까지: 「파일\t칸목록순번:문단\t[줄 시작]」(칸 목록 순번은 isCell 목록 차례)
use rhwp::document_core::DocumentCore;

fn main() {
    let cells = std::env::var("CLAUDE_CELLS").is_ok();
    for path in std::env::args().skip(1) {
        // CLAUDE_METRICS_DIR 가 있으면 <폴더>/<파일 이름>.json 의 글꼴 폭 표를 등록한다(에디터와 같은 조건)
        if let Ok(dir) = std::env::var("CLAUDE_METRICS_DIR") {
            let stem = std::path::Path::new(&path).file_stem().map(|s| s.to_string_lossy().to_string()).unwrap_or_default();
            if let Ok(json) = std::fs::read_to_string(std::path::Path::new(&dir).join(format!("{stem}.json"))) {
                let _ = rhwp::renderer::font_metrics_data::claude_register_font_metrics(&json);
            }
        }
        let data = std::fs::read(&path).expect("파일 읽기");
        let core = DocumentCore::from_bytes(&data).expect("문서 열기");
        let cm: serde_json::Value = serde_json::from_str(&core.get_cursor_model_json()).expect("커서 모형");
        println!("{}\tPAGES\t{}", path, core.page_count());
        // CLAUDE_SVG=<폴더> 이면 쪽마다 SVG 를 <폴더>/<쪽>.svg 로
        if let Ok(dir) = std::env::var("CLAUDE_SVG") {
            for pg in 0..core.page_count() {
                if let Ok(svg) = core.render_page_svg_native(pg) {
                    let _ = std::fs::write(format!("{}/{}.svg", dir, pg), svg);
                }
            }
        }
        // CLAUDE_SEGV=1 이면 첫 구역 본문 문단마다 엔진이 가진 줄 배치의 vpos 를 stderr 로: 「SEGV 문단 [vpos/높이/간격...]」
        if std::env::var("CLAUDE_SEGV").is_ok() {
            if let Some(sec) = core.document().sections.first() {
                for (i, para) in sec.paragraphs.iter().enumerate() {
                    let v: Vec<String> = para
                        .line_segs
                        .iter()
                        .map(|s| format!("{}/{}/{}", s.vertical_pos, s.line_height, s.line_spacing))
                        .collect();
                    eprintln!("SEGV {} {}", i, v.join(" "));
                }
            }
        }
        // CLAUDE_ITEMS=1 이면 쪽마다 놓인 항목(문단, 표 조각의 행 범위)을 stderr 로
        if std::env::var("CLAUDE_ITEMS").is_ok() {
            eprintln!("{}", core.dump_page_items(None));
        }
        // 본문 문단이 놓인 쪽(score.mjs 문단 쪽 지표와 같은 getPageOfPosition): 「PP\t구역:문단\t쪽」
        for s in 0..64usize {
            let Ok(cnt) = core.get_paragraph_count_native(s) else { break };
            for p in 0..cnt {
                let page = core
                    .get_page_of_position_native(s, p)
                    .ok()
                    .and_then(|j| serde_json::from_str::<serde_json::Value>(&j).ok())
                    .and_then(|v| v["page"].as_i64())
                    .unwrap_or(-1);
                println!("{}\tPP\t{}:{}:{}", path, s, p, page);
                // CLAUDE_XP=문단 이면 그 본문 문단 글자마다 커서 x(pt): 「XP\t구역:문단:글자\tx:y」
                // CLAUDE_XP=all 이면 모든 본문 문단의 앞 글자 몇 개(CLAUDE_XPN, 기본 6)
                let xp = std::env::var("CLAUDE_XP").ok();
                let all = xp.as_deref() == Some("all");
                if all || xp.and_then(|v| v.parse::<usize>().ok()) == Some(p) {
                    let n = if all {
                        std::env::var("CLAUDE_XPN").ok().and_then(|v| v.parse().ok()).unwrap_or(6)
                    } else {
                        400usize
                    };
                    for c in 0..n {
                        let Some(r) = core
                            .get_cursor_rect_native(s, p, c)
                            .ok()
                            .and_then(|j| serde_json::from_str::<serde_json::Value>(&j).ok())
                        else {
                            break;
                        };
                        let px = r["x"].as_f64().unwrap_or(-1.0);
                        let py = r["y"].as_f64().unwrap_or(-1.0);
                        println!("{}\tXP\t{}:{}:{}\t{:.2}:{:.1}", path, s, p, c, px * 0.75, py);
                    }
                }
                // CLAUDE_VY=1 이면 문단 첫 글자 커서의 쪽과 y(px)도: 「VY\t구역:문단\t쪽:y:높이」
                if std::env::var("CLAUDE_VY").is_ok() {
                    let r = core
                        .get_cursor_rect_native(s, p, 0)
                        .ok()
                        .and_then(|j| serde_json::from_str::<serde_json::Value>(&j).ok());
                    if let Some(r) = r {
                        println!(
                            "{}\tVY\t{}:{}\t{}:{}:{}",
                            path,
                            s,
                            p,
                            r["pageIndex"].as_i64().unwrap_or(-1),
                            r["y"].as_f64().unwrap_or(-1.0),
                            r["height"].as_f64().unwrap_or(-1.0)
                        );
                    }
                }
            }
        }
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
