// ==== find ====
            if !matches!(&para.controls[inner_control_idx], Control::Picture(_)) {
                return Err(HwpError::RenderError(
                    "지정된 셀 내 컨트롤이 그림이 아닙니다".to_string(),
                ));
            }

            let text_chars: Vec<char> = para.text.chars().collect();
// ==== replace ====
            // [claude-hwpx cell-table-delete] 칸 안의 표도 지운다. 표 속 표를 지울 경로 메서드가 없어 다른 세션이 「에디터나 엔진
            // 메서드로 지울 방법을 찾지 못했다」며 멈췄다(2026-10-17 문항 4 자료 1 의 표). 본문 표는 deleteTableControl 이 맡는다
            if !matches!(&para.controls[inner_control_idx], Control::Picture(_) | Control::Table(_)) {
                return Err(HwpError::RenderError(
                    "지정된 셀 내 컨트롤이 그림이나 표가 아닙니다".to_string(),
                ));
            }

            let text_chars: Vec<char> = para.text.chars().collect();
// ==== next ====
            Self::reflow_paragraph_line_segs_after_control_delete(para, &self.styles, self.dpi);
        }

        let section = &mut self.document.sections[section_idx];
// ==== replace ====
            Self::reflow_paragraph_line_segs_after_control_delete(para, &self.styles, self.dpi);
        }
        // [claude-hwpx cell-table-delete] 개체를 지운 칸 문단 뒤의 세로 위치를 다시 매기고, 안쪽 표부터 높이를 다시 재 바깥 표를
        // 편집됨으로 표시한다(쪽 나누기 앞 맞춤이 바깥 표 높이와 그 줄을 줄인다). 그림 크기 바꾸기(cell-pic-resize-nested)와 같은 순서
        {
            let cpi = path[path.len() - 1].2;
            self.recalculate_cell_paragraph_vpos_by_path(section_idx, parent_para_idx, &path, cpi, None);
            self.claude_init_measure_offsets();
            self.claude_sync_nested_tac(section_idx, parent_para_idx, path[0].0);
            if let Ok(t) = self.get_table_mut(section_idx, parent_para_idx, path[0].0) {
                t.dirty = true;
            }
            self.sync_tac_table_host_line(section_idx, parent_para_idx, path[0].0);
        }

        let section = &mut self.document.sections[section_idx];
