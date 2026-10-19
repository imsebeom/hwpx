// ==== find ====
                y_offset = hcursor.vpos_adjust(y_offset, item_para, paragraphs, styles);
// ==== replace ====
                // [claude-hwpx restrict-float-defer] 단 첫 항목이 미룬 표면(다음 항목이 앞 쪽에서 이어지는 줄이거나 표 문단보다 두 칸 이상 뒤)
                // 앵커 문단의 저장 위치는 앞 쪽 것이다 — 그 vpos 로 스냅하지 않고 표 아래로 순서대로 잇는다
                if self.profile.get().hwpx_container()
                    && item_ordinal == 1
                    && matches!(
                        col_content.items.first(),
                        Some(PageItem::Table { para_index, .. } | PageItem::PartialTable { para_index, .. })
                            if *para_index < item_para
                                && (*para_index + 1 < item_para
                                    || matches!(item, PageItem::PartialParagraph { start_line, .. } if *start_line > 0))
                    )
                {
                    hcursor.prev_layout_para = None;
                }
                y_offset = hcursor.vpos_adjust(y_offset, item_para, paragraphs, styles);
