// ==== find ====
static CLAUDE_ZERO_MAP: [u8; 28] = [0; 28];
// ==== replace ====
/// [claude-hwpx word-compat-lineheight] 등록한 글꼴의 세로 수치(hhea ascender, descender, lineGap 을 em 으로 나눈 값). 보통 얼굴만 담는다
static CLAUDE_RUNTIME_VM: OnceLock<std::sync::RwLock<HashMap<String, [f64; 3]>>> = OnceLock::new();

/// 이 이름으로 등록한 글꼴의 세로 수치 [ascender, descender, lineGap](em 비율). Word 호환 문서의 줄 높이에 쓴다
pub(crate) fn claude_font_vm(name: &str) -> Option<[f64; 3]> {
    CLAUDE_RUNTIME_VM.get()?.read().ok()?.get(name).copied()
}
static CLAUDE_ZERO_MAP: [u8; 28] = [0; 28];
// ==== next ====
        let bold = face.get("bold").and_then(|v| v.as_bool()).unwrap_or(false);
        let already = map
// ==== replace ====
        let bold = face.get("bold").and_then(|v| v.as_bool()).unwrap_or(false);
        // [claude-hwpx word-compat-lineheight] 세로 수치는 폭 표와 따로 둔다(내장 표가 있어 폭 표를 건너뛰는 글꼴도 담는다)
        if !bold {
            let vm: Vec<f64> = face.get("vm").and_then(|v| v.as_array()).into_iter().flatten()
                .filter_map(|x| x.as_i64())
                .map(|x| x as f64 / em as f64)
                .collect();
            if vm.len() == 3 && vm[0] > 0.0 {
                if let Ok(mut table) = CLAUDE_RUNTIME_VM.get_or_init(|| std::sync::RwLock::new(HashMap::new())).write() {
                    table.entry(name.to_string()).or_insert([vm[0], vm[1], vm[2]]);
                }
            }
        }
        let already = map
