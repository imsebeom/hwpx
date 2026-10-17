// ==== find ====
    pub kerning: bool,
    /// 자간 (px)
// ==== replace ====
    pub kerning: bool,
    /// [claude-hwpx use-font-space] 글자 모양의 「글꼴에 어울리는 빈칸」. 켜지면 빈칸은 글꼴 고유 폭이고, 꺼지면 한/글은 글자 크기의
    /// 절반을 쓴다(한/글 2024 실측: 글꼴 5종 × 장평과 자간 2종, PDF 글자 위치).
    #[serde(skip_serializing_if = "std::ops::Not::not")]
    pub use_font_space: bool,
    /// 자간 (px)
// ==== next ====
            kerning: false,
            letter_spacing: 0.0,
// ==== replace ====
            kerning: false,
            use_font_space: false,
            letter_spacing: 0.0,
