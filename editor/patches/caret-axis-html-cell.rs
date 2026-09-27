// ==== find ====
            cell_paras[cell_para_idx].insert_text_at(char_offset, &clip_text);

            let clip_char_shapes = parsed_paras[0].char_shapes.clone();
            let clip_char_offsets = parsed_paras[0].char_offsets.clone();
            Self::apply_clipboard_char_shapes_to_para(
                &mut cell_paras[cell_para_idx],
                char_offset,
// ==== replace ====
            // [claude-hwpx caret-axis html-cell] char_offset 은 캐럿 축
            let text_offset = crate::document_core::helpers::insert_text_at_caret(
                &mut cell_paras[cell_para_idx],
                char_offset,
                &clip_text,
            );

            let clip_char_shapes = parsed_paras[0].char_shapes.clone();
            let clip_char_offsets = parsed_paras[0].char_offsets.clone();
            Self::apply_clipboard_char_shapes_to_para(
                &mut cell_paras[cell_para_idx],
                text_offset,
