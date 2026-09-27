// ==== find ====
        let mut updates: Vec<CellUpdate> = Vec::new();
        let mut force_local_resize = false;
// ==== replace ====
        let mut updates: Vec<CellUpdate> = Vec::new();
        let mut force_local_resize = false;
        // [claude-hwpx row-resize-th] {"cellIdx":-1,"tableHeight":H} 가 오면 조절 뒤 표 높이를 다시 잰다(스튜디오 Ctrl+위/아래).
        let claude_table_height: Option<u32> = {
            let key = "\"tableHeight\"";
            trimmed.find(key).and_then(|at| {
                let rest = trimmed[at + key.len()..].trim_start().strip_prefix(':')?.trim_start();
                let end = rest.find(|c: char| !c.is_ascii_digit()).unwrap_or(rest.len());
                rest[..end].parse::<u32>().ok().filter(|h| *h > 0)
            })
        };
