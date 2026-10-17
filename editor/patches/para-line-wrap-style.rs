// ==== find ====
    pub break_latin_word: Option<String>,
}
// ==== replace ====
    pub break_latin_word: Option<String>,
    /// [claude-hwpx para-line-wrap] HWPX breakSetting@lineWrap 원문(BREAK/SQUEEZE/KEEP). None 이면 BREAK.
    /// SQUEEZE(한 줄로 입력)는 한/글이 줄을 나누지 않고 자간을 줄여 한 줄에 넣는다.
    pub hwpx_line_wrap: Option<String>,
}
// ==== next ====
            && self.break_latin_word == other.break_latin_word
    }
// ==== replace ====
            && self.break_latin_word == other.break_latin_word
            && self.hwpx_line_wrap == other.hwpx_line_wrap
    }
