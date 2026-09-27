// ==== find ====
    pub(crate) fn paginate(&mut self) {
        self.pending_pagination_job = None;
// ==== replace ====
    pub(crate) fn paginate(&mut self) {
        self.pending_pagination_job = None;
        // [claude-hwpx tac-host-sync-paginate] 편집한 글자처럼 취급 표의 높이와 표를 담은 줄을 먼저 맞춘다
        self.claude_sync_dirty_tac_tables();
