// ==== find ====
                if vpos0_px > 0.0 && vpos0_px <= spacing_before + 0.5 {
                    y += vpos0_px;
                }
// ==== replace ====
                if vpos0_px > 0.0 && vpos0_px <= spacing_before + 0.5 {
                    y += vpos0_px;
                } else if self.profile.get().hwpx_container()
                    && para.and_then(|p| p.line_segs.first()).is_some_and(|ls| {
                        ls.tag & LineSeg::TAG_IMPLEMENTATION_PROPERTY != 0
                            || hwpunit_to_px(ls.vertical_pos, self.dpi) > spacing_before + 0.5
                    })
                {
                    // [claude-hwpx pagetop-sb-synth] 엔진이 만든 줄이거나 첫 줄 vpos 가 쪽 기준이 아니면(구역 처음부터 이어 센 값) 쪽 머리 증거가 없다 —
                    // 한/글 HWPX 는 쪽 머리 위 간격을 늘 남긴다(새 조판 256/256). vpos 0(트림한 저장본)은 그대로 버린다
                    y += spacing_before;
                }
