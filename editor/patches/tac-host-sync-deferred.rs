// ==== find ====
        self.pending_pagination_job = None;
        let Some(descriptor) = self.deferred_pagination_descriptor.clone() else {
// ==== replace ====
        self.pending_pagination_job = None;
        // [claude-hwpx tac-host-sync-deferred] 미룬 쪽 나누기도 시작 전에 편집한 글자처럼 취급 표를 맞춘다
        self.claude_sync_dirty_tac_tables();
        let Some(descriptor) = self.deferred_pagination_descriptor.clone() else {
