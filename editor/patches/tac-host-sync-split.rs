// ==== find ====
        // raw 스트림 무효화, section dirty, 재페이지네이션
        self.document.sections[section_idx].raw_stream = None;
        self.mark_section_dirty(section_idx);
        self.paginate_if_needed();

        self.event_log.push(DocumentEvent::CellTextChanged {
// ==== replace ====
        // raw 스트림 무효화, section dirty, 재페이지네이션
        self.document.sections[section_idx].raw_stream = None;
        // [claude-hwpx tac-host-sync-split] 칸 문단 나누기(Enter)와 합치기에도 표 높이를 맞춘다
        self.sync_tac_table_host_line(section_idx, parent_para_idx, control_idx);
        self.mark_section_dirty(section_idx);
        self.paginate_if_needed();

        self.event_log.push(DocumentEvent::CellTextChanged {
