// ==== find ====
    pub fn delete_range_caret_native(
// ==== replace ====
    /// [claude-hwpx note-renumber] 끝난 뒤 각주, 미주 번호를 문서 순서대로 다시 매긴다(잘라 붙인 각주가 옛 번호를 가져가던 문제)
    #[allow(clippy::too_many_arguments)]
    pub fn delete_range_caret_native(&mut self, section_idx: usize, start_para: usize, start_caret: usize, end_para: usize, end_caret: usize, cell_ctx: Option<(usize, usize, usize)>) -> Result<String, HwpError> {
        let r = self.delete_range_caret_native_claude_inner(section_idx, start_para, start_caret, end_para, end_caret, cell_ctx);
        if r.is_ok() {
            self.claude_renumber_notes();
        }
        r
    }

    #[allow(clippy::too_many_arguments)]
    fn delete_range_caret_native_claude_inner(
// ==== next ====
    pub fn delete_range_caret_in_cell_by_path(
// ==== replace ====
    /// [claude-hwpx note-renumber] 끝난 뒤 각주, 미주 번호를 문서 순서대로 다시 매긴다(잘라 붙인 각주가 옛 번호를 가져가던 문제)
    #[allow(clippy::too_many_arguments)]
    pub fn delete_range_caret_in_cell_by_path(&mut self, section_idx: usize, parent_para_idx: usize, path: &[(usize, usize, usize)], start_para: usize, start_caret: usize, end_para: usize, end_caret: usize) -> Result<String, HwpError> {
        let r = self.delete_range_caret_in_cell_by_path_claude_inner(section_idx, parent_para_idx, path, start_para, start_caret, end_para, end_caret);
        if r.is_ok() {
            self.claude_renumber_notes();
        }
        r
    }

    #[allow(clippy::too_many_arguments)]
    fn delete_range_caret_in_cell_by_path_claude_inner(
