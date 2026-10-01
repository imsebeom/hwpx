// ==== find ====
            _ => return Err(JsValue::from_str("mode 는 0~6")),
// ==== replace ====
            // [claude-hwpx cell-pic-caret-wasm] 7: offset 을 컨트롤 번호로 받아 그 컨트롤 바로 앞의 캐럿 칸
            7 => axis::claude_control_caret_offset(para, off),
            _ => return Err(JsValue::from_str("mode 는 0~7")),
