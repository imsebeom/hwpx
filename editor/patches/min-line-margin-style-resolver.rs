// ==== find ====
    used > 0.0 && full_px > 0.0 && full_px - used < full_px * 0.25
}
// ==== replace ====
    // [claude-hwpx min-line-margin] 여백을 뺀 줄 폭이 1440HU(dpi 96 에서 19.2px)보다 좁아도 무시한다(새 정답본 칸 줄 211/211: horzpos 0, 폭 1440)
    used > 0.0
        && full_px > 0.0
        && (full_px - used < full_px * 0.25
            || full_px - used < 1440.0 / 7200.0 * crate::renderer::DEFAULT_DPI)
}
