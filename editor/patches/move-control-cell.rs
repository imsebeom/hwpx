// ==== find ====
        Ok(format!("{{\"ok\":true,\"ppi\":{},\"ci\":{},\"moved\":true}}", insert_at, new_ci))
    }
// ==== replace ====
        Ok(format!("{{\"ok\":true,\"ppi\":{},\"ci\":{},\"moved\":true}}", insert_at, new_ci))
    }

    /// [claude-hwpx move-control-cell] 칸 안 개체(표 속 표, 칸 그림)를 같은 칸 문단 목록의 dst 자리(그 문단 앞, 문단 수면 맨 끝)로 옮긴다.
    ///
    /// `table_path`: 개체까지의 경로 — 앞쪽은 개체를 담은 칸(마지막 칸 항목의 문단 번호 = 개체 문단), 마지막 항목의 컨트롤 번호 = 개체.
    /// 스튜디오가 표 속 표를 끌어 놓을 때 부른다. 종전에는 끌기가 바깥 표 번호만 써서 바깥 표가 통째로 옮겨졌다(2026-10-07 사용자 보고).
    /// 개체만 담은 문단(표 속 표는 대개 이렇다)만 문단째 옮긴다. 글과 같이 있는 개체는 거절한다(바깥 표는 건드리지 않는다).
    /// 반환: `{"ok":true,"cellPara":<새 문단>,"moved":true|false}`
    pub fn claude_move_control_in_cell(
        &mut self,
        section_idx: usize,
        parent_para_idx: usize,
        table_path: &[(usize, usize, usize)],
        dst: usize,
    ) -> Result<String, HwpError> {
        if table_path.len() < 2 {
            return Err(HwpError::RenderError("칸 안 개체 경로가 아니다".to_string()));
        }
        let cell_path = &table_path[..table_path.len() - 1];
        let host_para = cell_path[cell_path.len() - 1].2;
        let control_idx = table_path[table_path.len() - 1].0;
        let insert_at = {
            let paras = self.get_cell_paragraphs_mut_by_path(section_idx, parent_para_idx, cell_path)?;
            let n = paras.len();
            if host_para >= n || dst > n {
                return Err(HwpError::RenderError("칸 문단 범위 초과".to_string()));
            }
            let host = &paras[host_para];
            match host.controls.get(control_idx) {
                Some(Control::Table(_)) | Some(Control::Picture(_)) | Some(Control::Shape(_)) => {}
                _ => return Err(HwpError::RenderError("옮길 수 있는 개체가 아니다".to_string())),
            }
            let sole = host.controls.len() == 1 && host.text.trim().is_empty();
            if !sole {
                return Err(HwpError::RenderError("칸 안에서는 개체만 담은 문단만 옮긴다".to_string()));
            }
            if dst == host_para || dst == host_para + 1 {
                return Ok(format!("{{\"ok\":true,\"cellPara\":{},\"moved\":false}}", host_para));
            }
            let mut p = paras.remove(host_para);
            let reset = |c: &mut crate::model::shape::CommonObjAttr| {
                if !c.treat_as_char {
                    c.vertical_offset = 0;
                }
            };
            match p.controls.get_mut(control_idx) {
                Some(Control::Table(t)) => reset(&mut t.common),
                Some(Control::Picture(pic)) => reset(&mut pic.common),
                Some(Control::Shape(s)) => reset(s.common_mut()),
                _ => {}
            }
            let at = if dst > host_para { dst - 1 } else { dst };
            paras.insert(at.min(paras.len()), p);
            at.min(n - 1)
        };
        let count = self
            .get_cell_paragraphs_mut_by_path(section_idx, parent_para_idx, cell_path)?
            .len();
        let mut path = cell_path.to_vec();
        for i in 0..count {
            if let Some(last) = path.last_mut() {
                last.2 = i;
            }
            self.reflow_cell_paragraph_by_path(section_idx, parent_para_idx, &path, i);
        }
        self.recalculate_cell_paragraph_vpos_by_path(section_idx, parent_para_idx, cell_path, 0, None);
        self.mark_cell_control_dirty(section_idx, parent_para_idx, cell_path[0].0);
        self.document.sections[section_idx].raw_stream = None;
        self.mark_section_dirty(section_idx);
        self.paginate_if_needed();
        Ok(format!("{{\"ok\":true,\"cellPara\":{},\"moved\":true}}", insert_at))
    }
