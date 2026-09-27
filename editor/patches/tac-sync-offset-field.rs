// ==== find ====
    #[doc(hidden)]
    pub dirty: bool,
// ==== replace ====
    #[doc(hidden)]
    pub dirty: bool,
    /// [claude-hwpx tac-sync-offset] 처음 쪽을 나눌 때 잰 「적힌 높이 0 인 사본으로 잰 높이 − 적힌 표 높이」(HWPUNIT).
    /// 편집 뒤 표 높이는 잰 높이에서 이 값을 뺀다. None 이면 아직 재지 않았다.
    #[doc(hidden)]
    #[serde(skip)]
    pub claude_measure_offset: Option<i32>,
