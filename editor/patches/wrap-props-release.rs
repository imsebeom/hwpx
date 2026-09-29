// ==== find ====
        let band_geometry_before = self
            .resolve_picture_control_ref(section_idx, parent_para_idx, control_idx)
            .ok()
            .map(|pic| picture_band_geometry(&pic.common));
// ==== replace ====
        let band_geometry_before = self
            .resolve_picture_control_ref(section_idx, parent_para_idx, control_idx)
            .ok()
            .map(|pic| picture_band_geometry(&pic.common));
        // [claude-hwpx wrap-props-release] 옛 그림 띠 범위를 속성을 바꾸기 **전에** 기억해 둔다. 바꾼 뒤에 재면 새 위치의 띠가
        // 나와, 그림을 내렸다가 다시 올리면 그림이 떠난 문단이 옛 자리의 좁은 줄을 그대로 갖고 남았다(2026-09-29 사용자 발견)
        let claude_old_band = self
            .picture_band_owning_body_paragraph(section_idx, parent_para_idx)
            .filter(|(owner, _, _)| *owner == parent_para_idx)
            .map(|(_, range, _)| range);
// ==== next ====
            let _ = self.apply_body_edit_through_picture_band(section_idx, parent_para_idx, |_| {});
        }
// ==== replace ====
            let _ = self.apply_body_edit_through_picture_band(section_idx, parent_para_idx, |_| {});
            // 새 띠에 들지 않는 옛 띠 문단은 폭 전체로 다시 나눈다. 새 띠를 못 만들면(지원하지 않는 배치, 문단 간격 등)
            // 호스트까지 푼다 — 옛 자리의 좁은 줄로 남기는 것보다 겹침이 적다
            if let Some(old) = claude_old_band {
                let new_band = self
                    .picture_band_owning_body_paragraph(section_idx, parent_para_idx)
                    .filter(|(owner, _, _)| *owner == parent_para_idx)
                    .map(|(_, range, _)| range);
                let from = new_band.as_ref().map_or(old.start, |range| range.end.max(old.start + 1));
                if from < old.end {
                    let stored_end = crate::renderer::composer::paragraph_flow_end(
                        &self.document.sections[section_idx].paragraphs[from],
                    );
                    for idx in from..old.end {
                        self.reflow_paragraph(section_idx, idx);
                    }
                    let hwp3 = self.document.layout_profile().hwp3_layout();
                    crate::renderer::composer::recalculate_section_vpos(
                        &mut self.document.sections[section_idx].paragraphs,
                        from,
                        Some(from..old.end),
                        stored_end,
                        &self.styles,
                        self.dpi,
                        hwp3,
                    );
                }
            }
        }
