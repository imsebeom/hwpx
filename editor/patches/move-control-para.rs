    /// [claude-hwpx move-control-para] 본문 개체(표, 그림, 도형)를 문단 목록의 dst 자리(그 문단 앞, 문단 수면 맨 끝)로 옮긴다.
    /// 스튜디오 끌어 옮기기가 마우스를 놓을 때 부른다. 종전에는 끄는 동안 오프셋만 바꿔 원래 문단 자리가 비고
    /// 문단 관계가 그대로라 문서에 여백이 생겼다(2026-09-28 사용자 요청).
    /// - 개체만 담은 문단이면 문단째 옮긴다(문단 모양, 줄 배치 보존, 빈 문단이 남지 않는다).
    /// - 글이나 다른 개체와 같이 있으면 개체만 떼어 새 문단으로 옮긴다.
    /// - 떠 있는 개체는 세로 오프셋을 0 으로 해 새 문단 윗변에 붙인다.
    /// 반환: `{"ok":true,"ppi":<새 문단>,"ci":<새 컨트롤>}`
    pub fn claude_move_control_to_para(
        &mut self,
        section_idx: usize,
        para_idx: usize,
        control_idx: usize,
        dst: usize,
    ) -> Result<String, HwpError> {
        let para_count = self
            .document
            .sections
            .get(section_idx)
            .ok_or_else(|| HwpError::RenderError(format!("구역 {} 범위 초과", section_idx)))?
            .paragraphs
            .len();
        if para_idx >= para_count || dst > para_count {
            return Err(HwpError::RenderError("문단 범위 초과".to_string()));
        }
        let host = &self.document.sections[section_idx].paragraphs[para_idx];
        match host.controls.get(control_idx) {
            Some(Control::Table(_)) | Some(Control::Picture(_)) | Some(Control::Shape(_)) => {}
            _ => return Err(HwpError::RenderError("옮길 수 있는 개체가 아니다".to_string())),
        }
        let sole = host.controls.len() == 1 && host.text.trim().is_empty();
        if sole && (dst == para_idx || dst == para_idx + 1) {
            return Ok(format!("{{\"ok\":true,\"ppi\":{},\"ci\":{},\"moved\":false}}", para_idx, control_idx));
        }
        let (mut moved, new_ci, insert_at) = if sole {
            let p = self.document.sections[section_idx].paragraphs.remove(para_idx);
            // 조판, 측정 캐시는 문단 번호로 붙어 있다 — 같이 빼지 않으면 뒤 문단이 옛 번호의 측정값(다른 표 높이)으로 그려졌다
            self.remove_composed_paragraph(section_idx, para_idx);
            let at = if dst > para_idx { dst - 1 } else { dst };
            (p, control_idx, at)
        } else {
            // 사용자 클립보드는 건드리지 않는다 — 잠시 빼 두었다가 되돌린다
            let saved = self.clipboard.take();
            let copied = self.copy_control_native(section_idx, para_idx, &[], control_idx);
            let p = self.clipboard.take().and_then(|c| c.paragraphs.into_iter().next());
            self.clipboard = saved;
            copied?;
            let mut p = p.ok_or_else(|| HwpError::RenderError("개체 복사 실패".to_string()))?;
            // [claude-hwpx move-float-line] 떠 있는 그림, 도형은 줄을 차지하지 않는다. 복사가 줄 높이를 개체 높이로
            // 적어 두면 자리 차지 그림은 렌더러가 그림 높이만큼 흐름을 또 내려 그림 아래에 그림 높이만큼 빈 자리가 생겼다
            // (2026-09-29 사용자 발견). 한글은 이 문단 줄을 보통 글자 줄로 적는다 — 원래 문단 첫 줄의 글자 규격을 옮긴다
            let floating = match p.controls.first() {
                Some(Control::Picture(pic)) => !pic.common.treat_as_char,
                Some(Control::Shape(shape)) => !shape.common().treat_as_char,
                _ => false,
            };
            if floating {
                if let Some(line) = self.document.sections[section_idx].paragraphs[para_idx]
                    .line_segs
                    .first()
                    .cloned()
                {
                    for seg in &mut p.line_segs {
                        seg.line_height = line.line_height;
                        seg.text_height = line.text_height;
                        seg.baseline_distance = line.baseline_distance;
                        seg.line_spacing = line.line_spacing;
                    }
                }
            }
            self.delete_control_native(section_idx, para_idx, control_idx)?;
            (p, 0, dst)
        };
        let reset = |c: &mut crate::model::shape::CommonObjAttr| {
            if !c.treat_as_char {
                c.vertical_offset = 0;
            }
        };
        match moved.controls.get_mut(new_ci) {
            Some(Control::Table(t)) => {
                reset(&mut t.common);
                if !t.common.treat_as_char && t.raw_ctrl_data.len() >= crate::model::shape::common_obj_offsets::V_OFFSET.end {
                    t.raw_ctrl_data[crate::model::shape::common_obj_offsets::V_OFFSET]
                        .copy_from_slice(&0u32.to_le_bytes());
                }
            }
            Some(Control::Picture(p)) => reset(&mut p.common),
            Some(Control::Shape(s)) => reset(s.common_mut()),
            _ => {}
        }
        let paras = &mut self.document.sections[section_idx].paragraphs;
        let insert_at = insert_at.min(paras.len());
        paras.insert(insert_at, moved);
        self.insert_composed_paragraph(section_idx, insert_at);
        self.document.sections[section_idx].raw_stream = None;
        // 옮긴 문단과 그 뒤 문단의 저장 세로 위치를 다시 매긴다. 옮긴 문단에 남은 옛 쪽 경계(vpos 0)는 무시한다
        let from = insert_at.min(para_idx);
        let hwp3 = self.document.layout_profile().hwp3_layout();
        crate::renderer::composer::recalculate_section_vpos(
            &mut self.document.sections[section_idx].paragraphs,
            from,
            Some(insert_at..insert_at + 1),
            None,
            &self.styles,
            self.dpi,
            hwp3,
        );
        // [claude-hwpx move-band] 떠 있는 그림을 옮긴 새 문단은 뒤 문단들과 그림 띠를 이룬다. 다시 계산하지 않으면
        // 어울림 그림 옆으로 흘러야 할 다음 문단이 폭 전체로 남아 그림 위에 겹쳤다. 그림 속성 변경과 같은 재투영을 탄다
        // (띠를 만들 수 없는 배치면 조용히 지나간다)
        let _ = self.apply_body_edit_through_picture_band(section_idx, insert_at, |_| {});
        self.recompose_section(section_idx);
        self.paginate_if_needed();
        Ok(format!("{{\"ok\":true,\"ppi\":{},\"ci\":{},\"moved\":true}}", insert_at, new_ci))
    }

