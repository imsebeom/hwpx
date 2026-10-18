// ==== find ====
    pub fn paste_internal_native(
// ==== replace ====
    /// [claude-hwpx note-renumber] 끝난 뒤 각주, 미주 번호를 문서 순서대로 다시 매긴다(잘라 붙인 각주가 옛 번호를 가져가던 문제)
    #[allow(clippy::too_many_arguments)]
    pub fn paste_internal_native(&mut self, section_idx: usize, para_idx: usize, char_offset: usize) -> Result<String, HwpError> {
        let r = self.paste_internal_native_claude_inner(section_idx, para_idx, char_offset);
        if r.is_ok() {
            self.claude_renumber_notes();
        }
        r
    }

    #[allow(clippy::too_many_arguments)]
    fn paste_internal_native_claude_inner(
// ==== next ====
    pub fn paste_internal_in_cell_native(
// ==== replace ====
    /// [claude-hwpx note-renumber] 끝난 뒤 각주, 미주 번호를 문서 순서대로 다시 매긴다(잘라 붙인 각주가 옛 번호를 가져가던 문제)
    #[allow(clippy::too_many_arguments)]
    pub fn paste_internal_in_cell_native(&mut self, section_idx: usize, parent_para_idx: usize, control_idx: usize, cell_idx: usize, cell_para_idx: usize, char_offset: usize) -> Result<String, HwpError> {
        let r = self.paste_internal_in_cell_native_claude_inner(section_idx, parent_para_idx, control_idx, cell_idx, cell_para_idx, char_offset);
        if r.is_ok() {
            self.claude_renumber_notes();
        }
        r
    }

    #[allow(clippy::too_many_arguments)]
    fn paste_internal_in_cell_native_claude_inner(
// ==== next ====
    pub fn paste_internal_in_cell_by_path_native(
// ==== replace ====
    /// [claude-hwpx note-renumber] 끝난 뒤 각주, 미주 번호를 문서 순서대로 다시 매긴다(잘라 붙인 각주가 옛 번호를 가져가던 문제)
    #[allow(clippy::too_many_arguments)]
    pub fn paste_internal_in_cell_by_path_native(&mut self, section_idx: usize, parent_para_idx: usize, path: &[(usize, usize, usize)], char_offset: usize) -> Result<String, HwpError> {
        let r = self.paste_internal_in_cell_by_path_native_claude_inner(section_idx, parent_para_idx, path, char_offset);
        if r.is_ok() {
            self.claude_renumber_notes();
        }
        r
    }

    #[allow(clippy::too_many_arguments)]
    fn paste_internal_in_cell_by_path_native_claude_inner(
