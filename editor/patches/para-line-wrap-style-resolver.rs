// ==== find ====
    /// 문단 앞에서 항상 쪽 나눔 — attr1 bit 19
    pub page_break_before: bool,
}
// ==== replace ====
    /// 문단 앞에서 항상 쪽 나눔 — attr1 bit 19
    pub page_break_before: bool,
    /// [claude-hwpx para-line-wrap] 문단 모양 「한 줄로 입력」(HWPX lineWrap=SQUEEZE)
    pub line_wrap_squeeze: bool,
}
// ==== next ====
            page_break_before: false,
        }
    }
}
// ==== replace ====
            page_break_before: false,
            line_wrap_squeeze: false,
        }
    }
}
// ==== next ====
        page_break_before: (ps.attr1 >> 19) & 1 != 0,
    }
}
// ==== replace ====
        page_break_before: (ps.attr1 >> 19) & 1 != 0,
        line_wrap_squeeze: ps.hwpx_line_wrap.as_deref() == Some("SQUEEZE"),
    }
}
