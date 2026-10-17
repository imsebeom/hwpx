// ==== find ====
    matches!(cp,
        // 공백/제어문자
        0x0000..=0x0020 |
        // ASCII 구두점/기호 (영문자/숫자 제외)
        0x0021..=0x002F | 0x003A..=0x0040 | 0x005B..=0x0060 | 0x007B..=0x007F |
        // Latin-1 Supplement 구두점 (문자 제외)
        0x00A0..=0x00BF
    )
// ==== replace ====
    // [claude-hwpx lang-category] 한/글은 문장 부호도 범주가 고정이다(라틴, detect_lang_category, test/conformance/lab e7, e8).
    // 앞 글자를 따르는 것은 제어 문자와 빈칸뿐이다(빈칸을 두는 까닭은 detect_lang_category 주석).
    matches!(cp, 0x0000..=0x0020 | 0x007F | 0x00A0)
