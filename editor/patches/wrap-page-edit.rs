// ==== find ====
        let band = layout_picture_band(
            &section.paragraphs,
            host_index,
            column_width,
            &self.styles,
            self.dpi,
        )?;
// ==== replace ====
        // [claude-hwpx wrap-page-edit] 쪽, 종이 기준 그림을 그림 띠가 비키게 쪽 기하를 넘긴다(호출 직후 비운다)
        crate::renderer::float_placement::CLAUDE_BAND_PAGE
            .with(|cell| cell.set(self.claude_band_page(section_idx, host_index)));
        let band = layout_picture_band(
            &section.paragraphs,
            host_index,
            column_width,
            &self.styles,
            self.dpi,
        );
        crate::renderer::float_placement::CLAUDE_BAND_PAGE.with(|cell| cell.set(None));
        let band = band?;
// ==== next ====
        let Some(new_band) = layout_picture_band(
            &staged_paragraphs,
            host_index,
            column_width_px,
            &self.styles,
            self.dpi,
        ) else {
// ==== replace ====
        crate::renderer::float_placement::CLAUDE_BAND_PAGE
            .with(|cell| cell.set(self.claude_band_page(section_idx, host_index)));
        let new_band = layout_picture_band(
            &staged_paragraphs,
            host_index,
            column_width_px,
            &self.styles,
            self.dpi,
        );
        crate::renderer::float_placement::CLAUDE_BAND_PAGE.with(|cell| cell.set(None));
        let Some(new_band) = new_band else {
// ==== next ====
    /// Apply one body-paragraph mutation through its complete Picture band.
// ==== replace ====
    /// [claude-hwpx wrap-page-edit] 호스트 문단이 놓인 단을 기준으로 쪽 본문 영역과 종이의 위치(HWPUNIT, 단 좌표).
    fn claude_band_page(
        &self,
        section_idx: usize,
        host_index: usize,
    ) -> Option<crate::renderer::float_placement::ClaudeBandPage> {
        let section = self.document.sections.get(section_idx)?;
        let host_top = section.paragraphs.get(host_index)?.line_segs.first()?.vertical_pos;
        let column_def = Self::find_column_def_for_paragraph(&section.paragraphs, host_index);
        let layout =
            PageLayoutInfo::from_page_def(&section.section_def.page_def, &column_def, self.dpi);
        let column_index = self
            .para_column_map
            .get(section_idx)
            .and_then(|columns| columns.get(host_index))
            .copied()
            .unwrap_or(0) as usize;
        let column = layout
            .column_areas
            .get(column_index)
            .or_else(|| layout.column_areas.first())
            .unwrap_or(&layout.body_area);
        let hu = |px: f64| crate::renderer::px_to_hwpunit(px, self.dpi);
        Some(crate::renderer::float_placement::ClaudeBandPage {
            page_left: hu(layout.body_area.x - column.x),
            page_width: hu(layout.body_area.width),
            page_top: hu(layout.body_area.y - column.y),
            paper_left: hu(-column.x),
            paper_width: hu(layout.page_width),
            paper_top: hu(-column.y),
            host_top,
        })
    }

    /// Apply one body-paragraph mutation through its complete Picture band.
