    /// [claude-hwpx merge-edge] 합친 셀의 BorderFill: 주 셀(왼쪽 위)의 것에서 오른쪽 선은 오른쪽 가장자리 셀의,
    /// 아래 선은 아래 가장자리 셀의 것으로 바꾼다(한/글과 같게). rhwp 는 주 셀 것을 그대로 써서, 표 오른쪽 끝까지
    /// 합치면 없던 오른쪽 선이 생겼다.
    fn merged_cell_border_fill(&mut self, main: u16, right: u16, bottom: u16) -> u16 {
        use super::super::helpers::border_fills_equal;
        let get = |id: u16| {
            if id == 0 {
                None
            } else {
                self.document.doc_info.border_fills.get((id - 1) as usize).cloned()
            }
        };
        let Some(mut bf) = get(main) else { return main };
        if let Some(r) = get(right) {
            bf.borders[1] = r.borders[1];
        }
        if let Some(b) = get(bottom) {
            bf.borders[3] = b.borders[3];
        }
        bf.raw_data = None;
        if let Some(i) = self
            .document
            .doc_info
            .border_fills
            .iter()
            .position(|e| border_fills_equal(e, &bf))
        {
            return (i + 1) as u16;
        }
        self.document.doc_info.border_fills.push(bf);
        self.document.doc_info.raw_stream_dirty = true;
        self.rebuild_resolved_styles();
        self.document.doc_info.border_fills.len() as u16
    }

