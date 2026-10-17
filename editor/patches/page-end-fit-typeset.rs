// ==== find ====
        const DEFAULT_LAYOUT_DRIFT_SAFETY_PX: f64 = 4.0;
// ==== replace ====
        // [claude-hwpx page-end-fit] 한/글에는 이런 여유가 없다 — 남은 높이가 줄 높이를 넘기만 하면 넣는다(같으면 넘김).
        // 같을 때 넘기는 몫만 0.01px 로 남긴다(test/conformance/lab e13).
        const DEFAULT_LAYOUT_DRIFT_SAFETY_PX: f64 = 0.01;
