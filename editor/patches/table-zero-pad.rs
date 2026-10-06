// ==== find ====

    pub fn effective_padding(
        &self,
        table_padding: &crate::model::Padding,
    ) -> crate::model::Padding {
        let unspec = !self.apply_inner_margin && Self::table_padding_unspecified(table_padding);
        let pick = |c: i16, t: i16, unspec_axis: bool| -> i16 {
// ==== replace ====

    /// [claude-hwpx table-zero-pad] HWPX 에서 읽은 표(`raw_ctrl_data` 가 빈 표)의 「표 기본 여백 네 방향 0」은 미지정이 아니라 진짜 0 이다.
    ///
    /// 한/글 실측(2026-10-06): 칸 여백 141 이나 500, 표 안쪽 여백 네 방향 0, `hasMargin="0"` 인 1×1 표의 행은 9pt 줄 900 /
    /// 빈 문단 1000 으로 칸 여백이 들어가지 않는다. 같은 문서를 한/글로 HWP 로 저장했다 다시 열어도 같다. `hasMargin="1"` 이면
    /// 1182 / 1282. CORE 실적표(표 여백 0, 칸 141)는 이 규칙 때문에 내용으로 정해지는 행마다 282 씩 커져 9쪽 문서가 13쪽이 됐다.
    /// HWP5 원본은 #2195 stage50 의 86712 실측을 따라 종전대로 둔다.
    pub fn table_padding_unspecified_in(table: &Table) -> bool {
        !table.raw_ctrl_data.is_empty() && Self::table_padding_unspecified(&table.padding)
    }

    /// [claude-hwpx table-zero-pad] 표를 보고 고르는 `effective_padding`.
    pub fn effective_padding_in(&self, table: &Table) -> crate::model::Padding {
        if table.raw_ctrl_data.is_empty() && Self::table_padding_unspecified(&table.padding) {
            return self.effective_padding_with(&table.padding, false);
        }
        self.effective_padding(&table.padding)
    }

    pub fn effective_padding(
        &self,
        table_padding: &crate::model::Padding,
    ) -> crate::model::Padding {
        self.effective_padding_with(table_padding, true)
    }

    fn effective_padding_with(
        &self,
        table_padding: &crate::model::Padding,
        allow_unspecified: bool,
    ) -> crate::model::Padding {
        let unspec = allow_unspecified
            && !self.apply_inner_margin
            && Self::table_padding_unspecified(table_padding);
        let pick = |c: i16, t: i16, unspec_axis: bool| -> i16 {
