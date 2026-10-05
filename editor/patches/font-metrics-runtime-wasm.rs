// ==== find ====
/// HWP 파일에서 썸네일 이미지만 경량 추출 (전체 파싱 없이)
// ==== replace ====
/// [claude-hwpx font-metrics-runtime-wasm] 글꼴 폭 표를 등록한다(문서를 열기 전에 부른다). 반환: 새로 등록한 얼굴 수.
/// 형식은 `renderer::font_metrics_data::claude_register_font_metrics` 주석.
#[wasm_bindgen(js_name = registerFontMetrics)]
pub fn register_font_metrics(json: &str) -> Result<u32, JsValue> {
    crate::renderer::font_metrics_data::claude_register_font_metrics(json)
        .map(|added| added as u32)
        .map_err(|e| JsValue::from_str(&e))
}

/// 이 글꼴 이름의 폭 표가 빌드에 들어 있는가(별칭 포함). 없는 글꼴만 파일에서 읽어 등록한다.
#[wasm_bindgen(js_name = hasBuiltinFontMetric)]
pub fn has_builtin_font_metric(name: &str) -> bool {
    crate::renderer::font_metrics_data::claude_has_builtin_metric(name)
}

/// HWP 파일에서 썸네일 이미지만 경량 추출 (전체 파싱 없이)
