// ==== find ====
    pub(crate) fn recompose_section(&mut self, section_idx: usize) {
        self.invalidate_page_tree_cache();
// ==== replace ====
    pub(crate) fn recompose_section(&mut self, section_idx: usize) {
        self.invalidate_page_tree_cache();
        // [claude-hwpx measure-cache-shift] 표 측정 캐시는 (문단 번호, 컨트롤 번호)로 찾는다. 문단을 끼우거나 뺀 뒤 번호를 밀지 않은 경로(표 넣기 등)에서는
        // 뒤 표들이 다른 표의 높이를 받으니, 문단 수가 바뀌었으면 버리고 다시 잰다
        if let Some(ms) = self.measured_sections.get_mut(section_idx) {
            if ms.fallback_paragraphs.len() != self.document.sections[section_idx].paragraphs.len() {
                ms.tables.clear();
            }
        }
